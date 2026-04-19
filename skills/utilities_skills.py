import subprocess
import os

def create_alarm(seconds: str, message: str) -> str:
    """Définit une alarme qui sonnera dans X secondes."""
    try:
        sec = int(seconds)
        # On exécute la commande en arrière-plan (sleep puis notify-send + son)
        cmd = f'(sleep {sec} && notify-send "Alarme !" "{message}" -u critical && paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga || echo a) &'
        subprocess.Popen(cmd, shell=True)
        minutes = sec // 60
        leftover = sec % 60
        time_msg = f"{minutes} minute(s) et {leftover} seconde(s)" if minutes > 0 else f"{sec} secondes"
        return f"Alarme programmée pour dans {time_msg}. Raison : {message}"
    except Exception as e:
        return f"Impossible de créer l'alarme: {e}"

def write_note(filename: str, content: str) -> str:
    """Sauvegarde une note textuelle dans un fichier spécifié."""
    # S'assurer que ça va dans un dossier de notes
    folder = "/home/menma/menvis/notes"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{filename}.txt")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"J'ai pris en note ceci dans le fichier '{filename}.txt'."
    except Exception as e:
        return f"Erreur d'écriture du fichier : {e}"

UTILITIES_TOOLS = {
    'create_alarm': create_alarm,
    'write_note': write_note
}

UTILITIES_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'create_alarm',
            'description': 'Configure une minuterie / alarme qui se déclenchera dans un nombre précis de secondes.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'seconds': {'type': 'string', 'description': 'Temps en secondes avant l\'alarme'},
                    'message': {'type': 'string', 'description': 'Le message ou la raison de l\'alarme'}
                },
                'required': ['seconds', 'message']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'write_note',
            'description': 'Écrit, sauvegarde et enregistre du texte ou des notes dans un fichier.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string', 'description': 'Nom du fichier sans extension'},
                    'content': {'type': 'string', 'description': 'Le contenu à sauvegarder'}
                },
                'required': ['filename', 'content']
            }
        }
    }
]
