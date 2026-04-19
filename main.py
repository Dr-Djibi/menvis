import ollama
import sys
import os
import sys
import subprocess
from config import Config
from skills.registry import MENVIS_TOOLS, MENVIS_SCHEMAS
from skills.voice_input import listen_to_user
from skills.memory_skills import get_all_memory_context

def speak(text: str):
    """Utilise edge-tts pour prononcer la réponse et affiche la bulle virtuelle."""
    print(f"\n{Config.ASSISTANT_NAME}: {text}")
    
    # Lancement de la bulle visuelle J.A.R.V.I.S (non bloquant)
    ui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui/bubble.py")
    subprocess.Popen([sys.executable, ui_script, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try:
        # On exécute edge-tts dans un sous-processus sans bloquer la console de manière moche
        # La voix par défaut française de edge-tts est "fr-FR-DeniseNeural" ou "fr-FR-HenriNeural"
        voice = "fr-FR-HenriNeural" 
        subprocess.run(["edge-tts", "--voice", voice, "--text", text, "--play"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        pass # Si edge-tts n'est pas dispo, on a au moins le texte

class MenvisAssistant:
    def __init__(self):
        self.model = Config.MODEL_NAME
        self.system_prompt = Config.SYSTEM_PROMPT
        self.tools = MENVIS_TOOLS
        self.schemas = MENVIS_SCHEMAS

        # Injection de la mémoire persistante dans le prompt système
        persistent_memory = get_all_memory_context()
        full_system_prompt = self.system_prompt + "\n" + persistent_memory

        # Historique de conversation
        self.messages = [
            {'role': 'system', 'content': full_system_prompt}
        ]

    def ask(self, user_prompt: str):
        self.messages.append({'role': 'user', 'content': user_prompt})
        print(f"[*] {Config.ASSISTANT_NAME} réfléchit...")
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=self.schemas
            )
            
            message = response['message']

            if message.get('tool_calls'):
                for tool_call in message['tool_calls']:
                    func_name = tool_call['function']['name']
                    args = tool_call['function']['arguments']
                    
                    if Config.DEBUG:
                        print(f"  [DEBUG] Appel Outil: {func_name} | Args: {args}")

                    func = self.tools.get(func_name)
                    if func:
                        try:
                            result = func(**args)
                        except Exception as script_e:
                            result = f"Erreur du script: {script_e}"
                            
                        self.messages.append(message)
                        self.messages.append({
                            'role': 'tool', 
                            'name': func_name, 
                            'content': str(result)
                        })
                        
                        final_response = ollama.chat(model=self.model, messages=self.messages)
                        final_text = final_response['message']['content']
                        
                        self.messages.append({'role': 'assistant', 'content': final_text})
                        speak(final_text)

            else:
                final_text = message['content']
                self.messages.append({'role': 'assistant', 'content': final_text})
                speak(final_text)

        except Exception as e:
            print(f"[!] Erreur: Assurez-vous d'avoir lancé 'ollama run {self.model}'. Détails: {e}")

if __name__ == "__main__":
    assistant = MenvisAssistant()
    
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        assistant.ask(text)
    else:
        print("="*60)
        print(f"🚀 {Config.ASSISTANT_NAME} MAXIMUM EDITION INTÉGRÉE 🚀")
        print(" Outils Chargés : Recherche Web, KDE Connect, Alarmes,")
        print(" Fichiers, Volume, Info Système, Commandes Hyprland.")
        print(" Voix TTS activée (HenriNeural).")
        print(" Outils : Recherche Web, KDE Connect, Météo, etc.")
        print(" Tapez '/v' pour parler au microphone, '/q' pour quitter.")
        print("="*60)
        
        while True:
            try:
                # Écoute en boucle courte (4-5s) pour capter la parole
                texte_vocal = listen_to_user(silent_mode=True)
                
                # Si du texte a été détecté, on répond
                if texte_vocal:
                    # Empêche la boucle de s'écouter elle-même (mot de réveil ou arrêt)
                    if "arrête-toi" in texte_vocal.lower() or "désactiver" in texte_vocal.lower():
                        speak("Assistant désactivé. Au revoir.")
                        break
                    
                    assistant.ask(texte_vocal)
                    print("\n" + "="*40 + "\n") # Séparation visuelle après l'action
                    
            except KeyboardInterrupt:
                speak("Arrêt d'urgence. À bientôt.")
                print("\nArrêt forcé.")
                break
