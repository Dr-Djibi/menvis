import json
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
                            "model_decommissioned"]
    )


class MenvisAgent:
    def __init__(self):
        self.cascade  = Config.PROVIDER_CASCADE
        self._init_provider(self.cascade[0])

    # ── Initialisation d'un provider ─────────────────────────────────────────
    def _init_provider(self, provider: str):
        self.provider = provider
        self.client, self.model = _build_client(provider)
        label = PROVIDER_ICONS.get(provider, provider)
        print(f"[Menvis] Provider actif : {label}  |  Modèle : {self.model}")

        if self.model == "menvis-lite":
            self.tools, self.schemas = SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
        else:
            self.tools, self.schemas = MENVIS_TOOLS, MENVIS_SCHEMAS

    # ── Appel API avec cascade automatique ───────────────────────────────────
    def _call_api(self, kwargs: dict):
        providers_to_try = self.cascade[self.cascade.index(self.provider):]

        for provider in providers_to_try:
            if provider != self.provider:
                self._init_provider(provider)
                kwargs["model"] = self.model

            try:
                return self.client.chat.completions.create(**kwargs)

            except Exception as e:
                # Cas spécial : outils non supportés sur ce provider → réessayer sans
                if "tools" in kwargs and (
                    getattr(e, "status_code", None) == 400 or "400" in str(e)
                ):
                    print(f"[!] {PROVIDER_ICONS.get(provider)} : outils ignorés, mode simple...")
                    kw2 = {k: v for k, v in kwargs.items() if k != "tools"}
                    try:
                        return self.client.chat.completions.create(**kw2)
                    except Exception as e2:
                        e = e2  # propager l'erreur originale pour le fallback

                if _is_limit_error(e):
                    next_providers = self.cascade[self.cascade.index(provider) + 1:]
                    if next_providers:
                        print(f"[!] {PROVIDER_ICONS.get(provider)} indisponible → bascule sur {PROVIDER_ICONS.get(next_providers[0])}...")
                        continue
                    else:
                        raise RuntimeError("❌ Tous les providers sont épuisés.") from e
                else:
                    raise e

        raise RuntimeError("❌ Cascade épuisée sans réponse.")

    # ── Génération de réponse ────────────────────────────────────────────────
    def generate_response(self, user_prompt: str, persistent_memory: str = "") -> str:
        full_system_prompt = get_system_prompt()
        if persistent_memory:
            full_system_prompt += "\n\n# Mémoire Persistante\n" + persistent_memory

        messages = [
            {"role": "system",  "content": full_system_prompt},
            {"role": "user",    "content": user_prompt},
        ]

        kwargs = {
            "model":       self.model,
            "messages":    messages,
            "temperature": 0.3,
        }
        if self.schemas:
            kwargs["tools"] = [{"type": "function", "function": s} for s in self.schemas]

        response = self._call_api(kwargs)
        message  = response.choices[0].message

        # ── Appels d'outils ──────────────────────────────────────────────────
        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                if Config.DEBUG:
                    print(f"  [⚙️] Outil : {func_name} | Args : {args}")

                func = self.tools.get(func_name)
                result = func(**args) if func else f"Erreur: outil '{func_name}' inconnu."
                if func:
                    try:
                        result = func(**args)
                    except Exception as err:
                        result = f"Erreur outil : {err}"

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "name":         func_name,
                    "content":      str(result),
                })

            # Deuxième passe (résultats → LLM)
            try:
                final = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.3
                )
                return final.choices[0].message.content
            except Exception as e:
                return f"Erreur après l'action : {e}"

        return message.content
