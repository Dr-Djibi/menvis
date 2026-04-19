import json
import os

CACHE_FILE = "/home/menma/menvis/brain/notifications_cache.json"

def read_notifications() -> str:
    """Lit les notifications récentes du système et du téléphone Android (KDE Connect)."""
    if not os.path.exists(CACHE_FILE):
        return "Je n'ai reçu aucune notification pour le moment."
        
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            notifs = json.load(f)
            
        if not notifs:
            return "Aucune notification en attente."
            
        report = "Voici vos dernières notifications : \n"
        for n in notifs:
            report += f"- À {n['time']} depuis {n['source']} : '{n['title']}' -> {n['message']}\n"
            
        # Optionnel: on pourrait effacer le cache après l'avoir lu, mais le garder permet un historique
        return report
    except Exception as e:
        return f"Erreur de lecture du flux de notifications : {e}"

NOTIF_TOOLS = {
    'read_notifications': read_notifications
}

NOTIF_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'read_notifications',
            'description': 'Consulte le système central pour lire les dernières notifications reçues (SMS Android, applications PC, messagerie).',
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }
    }
]
