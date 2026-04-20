import ollama
import sys
import os
import subprocess
from config import Config
from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS, SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
from skills.voice_input import listen_to_user
from skills.memory_skills import get_all_memory_context
from openai import OpenAI
import json

def speak(text: str):
    """Utilise edge-tts pour prononcer la réponse et affiche la bulle virtuelle."""
    print(f"\n{Config.ASSISTANT_NAME}: {text}")

    # Lancement de la bulle visuelle J.A.R.V.I.S (non bloquant)
    ui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui/bubble.py")
    subprocess.Popen([sys.executable, ui_script, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        if os.getenv("MENVIS_NO_TTS"):
            return

        voice = "fr-FR-HenriNeural"
        subprocess.run(
            ["edge-tts", "--voice", voice, "--text", text, "--play"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass  # Si edge-tts n'est pas dispo, le texte est déjà affiché


class MenvisAssistant:
    def __init__(self):
        self.provider = Config.AI_PROVIDER
        
        if self.provider == "openrouter":
            self.model = Config.OPENROUTER_MODEL
            self.client = OpenAI(
                base_url=Config.OPENROUTER_BASE_URL,
                api_key=Config.OPENROUTER_API_KEY,
            )
        else:
            self.model = Config.OLLAMA_MODEL if Config.MODEL_NAME == "menvis-lite" else Config.MODEL_NAME
            self.client = None # Ollama via module direct

        # Détection du mode survie (modèle léger)
        if Config.MODEL_NAME == "menvis-lite":
            self.tools   = SURVIVAL_TOOLS
            self.schemas = SURVIVAL_SCHEMAS
        else:
            self.tools   = MENVIS_TOOLS
            self.schemas = MENVIS_SCHEMAS
            
        # Injection de la mémoire persistante dans le prompt système
        persistent_memory  = get_all_memory_context()
        full_system_prompt = Config.SYSTEM_PROMPT + "\n" + persistent_memory

        self.messages = [{'role': 'system', 'content': full_system_prompt}]

    # ──────────────────────────────────────────────────────────────────────
    #  Moteur Principal – Multi-Tâches
    # ──────────────────────────────────────────────────────────────────────
    def ask(self, user_prompt: str):
        self.messages.append({'role': 'user', 'content': user_prompt})

        try:
            if self.provider == "openrouter":
                # Version OpenRouter / OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=[{"type": "function", "function": s} for s in self.schemas] if self.schemas else None,
                    extra_headers={
                        "HTTP-Referer": "https://github.com/Dr-Djibi/menvis",
                        "X-Title": "Menvis Assistant",
                    }
                )
                message = response.choices[0].message
                # Conversion de l'objet message en dict compatible pour la suite si besoin
                role = message.role
                content = message.content
                tool_calls = message.tool_calls
                
                msg_dict = {'role': role, 'content': content}
                if tool_calls:
                    msg_dict['tool_calls'] = [
                        {
                            'id': tc.id,
                            'type': 'function',
                            'function': {
                                'name': tc.function.name,
                                'arguments': json.loads(tc.function.arguments)
                            }
                        } for tc in tool_calls
                    ]
            else:
                # Version Ollama
                response = ollama.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=self.schemas
                )
                msg_dict = response['message']

            # ── CAS 1 : Le modèle veut appeler des outils ──────────────────
            if msg_dict.get('tool_calls'):
                self.messages.append(msg_dict)
                tool_results = []

                for tool_call in msg_dict['tool_calls']:
                    func_name = tool_call['function']['name']
                    args      = tool_call['function']['arguments']

                    if Config.DEBUG:
                        print(f"  [⚙️] Outil: {func_name} | Args: {args}")

                    func = self.tools.get(func_name)
                    if func:
                        try:
                            result = func(**args)
                        except Exception as script_e:
                            result = f"Erreur d'exécution de {func_name}: {script_e}"
                    else:
                        result = f"Outil '{func_name}' non enregistré dans le registre."

                    tool_results.append(f"• {func_name}: {result}")

                    self.messages.append({
                        'role':    'tool',
                        'tool_call_id': tool_call.get('id', 'local'), # OpenAI a besoin de l'ID
                        'name':    func_name,
                        'content': str(result)
                    })

                # ── Une seule réponse finale qui synthétise tout ────────────
                if self.provider == "openrouter":
                    final_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=self.messages
                    )
                    final_text = final_response.choices[0].message.content
                else:
                    final_response = ollama.chat(model=self.model, messages=self.messages)
                    final_text = final_response['message']['content']

                self.messages.append({'role': 'assistant', 'content': final_text})
                speak(final_text)

            # ── CAS 2 : Réponse directe sans outil ─────────────────────────
            else:
                final_text = msg_dict['content']
                self.messages.append({'role': 'assistant', 'content': final_text})
                speak(final_text)

        except Exception as e:
            err = f"Erreur système ({self.provider}). Détail : {e}"
            print(f"[!] {err}")


# ──────────────────────────────────────────────────────────────────────────
#  Point d'entrée
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # ── Mode GUI ────────────────────────────────────────────────────────────
    if "--gui" in sys.argv:
        # Lance l'interface graphique CustomTkinter
        gui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "gui.py")
        subprocess.run([sys.executable, gui_script])
        sys.exit(0)

    # ── Mode terminal CLI ───────────────────────────────────────────────────
    assistant = MenvisAssistant()

    if len(sys.argv) > 1:
        # Commande unique passée en argument
        assistant.ask(" ".join(sys.argv[1:]))
    else:
        print(f"--- {Config.ASSISTANT_NAME} Édition Nexus (Local) ---")
        print(f"Prêt. Dites 'arrête-toi' pour quitter.")

        while True:
            try:
                texte_vocal = listen_to_user(silent_mode=True)

                if texte_vocal:
                    if any(w in texte_vocal.lower() for w in ["arrête-toi", "désactiver", "stop menvis"]):
                        speak("Déconnexion. À bientôt, Chef.")
                        break

                    assistant.ask(texte_vocal)
                    print("\n" + "─" * 40 + "\n")

            except KeyboardInterrupt:
                speak("Arrêt d'urgence. À bientôt.")
                print("\nArrêt forcé.")
                break
