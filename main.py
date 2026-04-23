import sys
import os
import subprocess
from config import Config
from agent.client import MenvisAgent
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
        pass  


if __name__ == "__main__":
    # ── Mode GUI ────────────────────────────────────────────────────────────
    if "--gui" in sys.argv:
        gui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "gui.py")
        subprocess.run([sys.executable, gui_script])
        sys.exit(0)

    # ── Initialisation de l'Agent ───────────────────────────────────────────
    agent = MenvisAgent()

    # ── Mode terminal CLI ───────────────────────────────────────────────────
    if len(sys.argv) > 1:
        # Commande unique passée en argument
        user_prompt = " ".join(sys.argv[1:])
        memory = get_all_memory_context()
        print(f"[*] Analyse de la requête...")
        response = agent.generate_response(user_prompt, persistent_memory=memory)
        speak(response)
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

                    memory = get_all_memory_context()
                    reponse_ia = agent.generate_response(texte_vocal, persistent_memory=memory)
                    speak(reponse_ia)
                    print("\n" + "─" * 40 + "\n")

            except KeyboardInterrupt:
                speak("Arrêt d'urgence. À bientôt.")
                print("\nArrêt forcé.")
                break
