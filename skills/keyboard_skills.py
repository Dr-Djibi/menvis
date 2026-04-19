import subprocess
import time

def type_text(text: str) -> str:
    """Tape physiquement du texte sur le clavier de l'utilisateur dans l'application actuellement activée."""
    try:
        # Court délai pour s'assurer qu'il a fini de parler ou que la fenêtre est prête
        time.sleep(0.5)
        # wtype est l'équivalent de xdotool mais pour Wayland (Hyprland)
        subprocess.run(["wtype", text], check=True)
        return f"J'ai tapé ce texte sur votre écran : '{text}'"
    except Exception as e:
        return f"Impossible d'utiliser le clavier virtuel fantôme. Assurez-vous d'avoir installé 'wtype' (yay -S wtype). Erreur: {e}"

KEYBOARD_TOOLS = {
    'type_text': type_text
}

KEYBOARD_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'type_text',
            'description': 'Simule des frappes au clavier réelles pour dicter/écrire du texte directement dans l\'application ou le champ de texte actuellement sélectionné par l\'utilisateur à l\'écran.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string', 'description': 'Le texte exact à écrire au clavier sur l\'écran de l\'utilisateur.'}
                },
                'required': ['text']
            }
        }
    }
]
