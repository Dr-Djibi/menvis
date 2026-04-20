import ollama
import sys
import os
import subprocess
from config import Config
from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS, SURVIVAL_TOOLS, SURVIVAL_SCHEMAS
from skills.voice_input import listen_to_user
from skills.memory_skills import get_all_memory_context

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
        self.model = Config.MODEL_NAME
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
        # print(f"[*] {Config.ASSISTANT_NAME} réfléchit...") # Caché pour la pureté du terminal

        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=self.schemas
            )
            message = response['message']

            # ── CAS 1 : Le modèle veut appeler des outils ──────────────────
            if message.get('tool_calls'):

                # Ajouter le message assistant (avec ses demandes d'outils) UNE seule fois
                self.messages.append(message)

                tool_results = []

                # Exécuter TOUS les outils demandés en séquence
                for tool_call in message['tool_calls']:
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

                    # Injecter le résultat de cet outil dans le contexte conversationnel
                    self.messages.append({
                        'role':    'tool',
                        'name':    func_name,
                        'content': str(result)
                    })

                if Config.DEBUG:
                    print(f"  [✅] {len(tool_results)} tâche(s) exécutée(s) :")
                    for r in tool_results:
                        print(f"    {r}")

                # ── Une seule réponse finale qui synthétise tout ────────────
                final_response = ollama.chat(model=self.model, messages=self.messages)
                final_text     = final_response['message']['content']
                self.messages.append({'role': 'assistant', 'content': final_text})
                speak(final_text)

            # ── CAS 2 : Réponse directe sans outil ─────────────────────────
            else:
                final_text = message['content']
                self.messages.append({'role': 'assistant', 'content': final_text})
                speak(final_text)

        except Exception as e:
            err = f"Erreur système. Vérifiez qu'Ollama tourne avec 'ollama run {self.model}'. Détail : {e}"
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
