import subprocess

def ring_phone() -> str:
    """Fait sonner le smartphone associé via KDE Connect pour le retrouver."""
    try:
        subprocess.run(["kdeconnect-cli", "--ring"], check=True)
        return "J'ai envoyé la commande pour faire sonner votre téléphone."
    except Exception as e:
        return f"Échec de la connexion avec KDE Connect: {e}"

def ping_phone(message: str) -> str:
    """Envoie une notification (ping) au téléphone via KDE Connect."""
    try:
        subprocess.run(["kdeconnect-cli", "--ping-msg", message], check=True)
        return f"J'ai envoyé la notification '{message}' à votre téléphone."
    except Exception as e:
        return f"Erreur lors de l'envoi de la notification: {e}"

PHONE_TOOLS = {
    'ring_phone': ring_phone,
    'ping_phone': ping_phone
}

PHONE_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'ring_phone',
            'description': 'Fait sonner très fort le téléphone portable de l\'utilisateur via KDEConnect pour l\'aider à le retrouver.',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'ping_phone',
            'description': 'Envoie une notification texte sur le téléphone portable de l\'utilisateur via KDEConnect.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': 'Le message de la notification'}
                },
                'required': ['message']
            }
        }
    }
]
