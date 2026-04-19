import subprocess

def control_media(action: str) -> str:
    """Contrôle la musique globale du système (Play, Pause, Suivant, Précédent)."""
    valid_actions = ["play-pause", "next", "previous", "stop"]
    action = action.lower()
    
    if action not in valid_actions:
        return f"Action invalide. Choisissez parmi: {', '.join(valid_actions)}"
        
    try:
        # On cible spécifiquement Firefox (pour votre PWA Spotify) via MPRIS
        subprocess.run(["playerctl", "--player=firefox,%any", action], check=True)
        # Sémantique améliorée pour le retour
        verb = "Mis en pause/Lecture" if action == "play-pause" else "Passé" if action == "next" else "Retourné"
        return f"Ordre '{verb}' exécuté sur le lecteur multimédia."
    except Exception as e:
         return f"Impossible de contrôler la musique. 'playerctl' est-il installé ? Erreur: {e}"

MEDIA_TOOLS = {
    'control_media': control_media
}

MEDIA_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'control_media',
            'description': 'Contrôle la musique en cours de lecture (Spotify, Navigateur, etc).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['play-pause', 'next', 'previous', 'stop'], 'description': 'L\'action à effectuer'}
                },
                'required': ['action']
            }
        }
    }
]
