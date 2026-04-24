import json
import time
from openai import OpenAI
from config import Config
from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS, SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
from prompts.system import get_system_prompt

# ─── Mapping provider → (base_url, api_key, model) ───────────────────────────
def _provider_credentials(provider: str) -> tuple[str, str, str]:
    mapping = {
        "groq":       (Config.GROQ_BASE_URL,       Config.GROQ_API_KEY,       Config.GROQ_MODEL),
        "gemini":     (Config.GEMINI_BASE_URL,      Config.GEMINI_API_KEY,     Config.GEMINI_MODEL),
        "openrouter": (Config.OPENROUTER_BASE_URL,  Config.OPENROUTER_API_KEY, Config.OPENROUTER_MODEL),
        "ollama":     (Config.OLLAMA_BASE_URL,      "ollama",                  Config.OLLAMA_MODEL),
    }
    return mapping[provider]


def _build_client(provider: str) -> tuple[OpenAI, str]:
    base_url, api_key, model = _provider_credentials(provider)
    return OpenAI(base_url=base_url, api_key=api_key or "none"), model


PROVIDER_ICONS = {
    "groq":       "☁️  Groq",
    "gemini":     "💎 Gemini",
    "openrouter": "🌐 OpenRouter",
    "ollama":     "💻 Ollama (local)",
}


# ─── Erreurs qui déclenchent le fallback ─────────────────────────────────────
def _is_limit_error(e: Exception) -> bool:
    """Retourne True si l'erreur est une limite de taux ou d'accès → on bascule."""
    code = getattr(e, "status_code", None)
    msg  = str(e).lower()
    return code in (429, 401, 403, 503) or any(
        k in msg for k in ["rate limit", "quota", "limit exceeded",
                            "too many", "unavailable", "decommissioned",
                            "model_decommissioned", "authentication"]
    )


class MenvisAgent:
    def __init__(self):
        self.cascade  = Config.PROVIDER_CASCADE
        self._init_provider(self.cascade[0])

    def _init_provider(self, provider: str):
        self.provider = provider
        self.client, self.model = _build_client(provider)
        label = PROVIDER_ICONS.get(provider, provider)
        print(f"[Menvis] Provider actif : {label}  |  Modèle : {self.model}")

        if self.model == "menvis-lite":
            self.tools, self.schemas = SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
        else:
            self.tools, self.schemas = MENVIS_TOOLS, MENVIS_SCHEMAS

    def _call_api(self, kwargs: dict):
        """Appel API avec gestion de la cascade."""
        providers_to_try = self.cascade[self.cascade.index(self.provider):]

        for provider in providers_to_try:
            if provider != self.provider:
                self._init_provider(provider)
                kwargs["model"] = self.model

            try:
                return self.client.chat.completions.create(**kwargs)

            except Exception as e:
                if "tools" in kwargs:
                    print(f"[DEBUG API Error] {e}") 
                    if (getattr(e, "status_code", None) == 400 or "400" in str(e)):
                        print(f"[!] {PROVIDER_ICONS.get(provider)} : outils non supportés, mode simple...")
                        kw_no_tools = {k: v for k, v in kwargs.items() if k != "tools"}
                        try:
                            return self.client.chat.completions.create(**kw_no_tools)
                        except Exception as e2:
                            e = e2

                if _is_limit_error(e):
                    next_idx = self.cascade.index(provider) + 1
                    if next_idx < len(self.cascade):
                        print(f"[!] {PROVIDER_ICONS.get(provider)} indisponible/limité → Fallback...")
                        continue
                    else:
                        raise e
                else:
                    raise e
        return None

    def generate_response(self, user_prompt: str, persistent_memory: str = "") -> str:
        """Génération de réponse avec boucle d'outils et anti-verbosité."""
        final_system_prompt = get_system_prompt()
        if persistent_memory:
            final_system_prompt += "\n\n# MÉMOIRE\n" + persistent_memory

        messages = [
            {"role": "system",  "content": final_system_prompt},
            {"role": "user",    "content": user_prompt},
        ]

        max_turns = 5
        for i in range(max_turns):
            kwargs = {
                "model":       self.model,
                "messages":    messages,
                "temperature": 0.1,
            }
            if self.schemas:
                # Nos schémas sont déjà au bon format {"type": "function", "function": ...}
                kwargs["tools"] = self.schemas

            response = self._call_api(kwargs)
            if not response: return "Erreur : Échec cascade."

            msg = response.choices[0].message
            
            # Anti-Yapping : Si le modèle commence à expliquer son plan au lieu de faire l'outil
            if not msg.tool_calls and i == 0:
                content = str(msg.content).lower()
                if any(x in content for x in ["vais prendre", "utiliser", "plan d'action", "étape"]):
                    if self.schemas:
                        messages.append({"role": "user", "content": "OPÉRATIONNEL : N'explique rien. Appelle l'outil immédiatement."})
                        continue

            messages.append(msg)
            if not msg.tool_calls: return msg.content

            # Exécution des outils
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                try: args = json.loads(tool_call.function.arguments)
                except: args = {}

                func = self.tools.get(func_name)
                if func:
                    try: result = func(**args)
                    except Exception as err: result = f"Erreur : {err}"
                else:
                    result = f"Outil '{func_name}' inconnu."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(result),
                })
        
        return "Erreur : Boucle infinie outils."
