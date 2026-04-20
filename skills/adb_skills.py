import subprocess
import os
import re

def _run_adb(args):
    """Exécute une commande ADB et retourne le résultat."""
    try:
        result = subprocess.run(["adb"] + args, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        return f"Erreur ADB : {str(e)}"

def connect_phone(address: str) -> str:
    """Connecte le téléphone via Wireless ADB (ex: 192.168.1.50:5555)."""
    res = _run_adb(["connect", address])
    if "connected" in res.lower():
        return f"Liaison Nexus établie avec {address}."
    return f"Échec de la liaison : {res}"

def list_phone_files(remote_path: str = "/sdcard/") -> str:
    """Explore les dossiers de votre téléphone."""
    res = _run_adb(["shell", "ls", "-F", remote_path])
    if not res: return "Dossier vide ou inaccessible."
    return f"Contenu de {remote_path} :\n{res}"

def read_last_sms(count: int = 5) -> str:
    """Lit les derniers SMS reçus sur le téléphone."""
    # Requête sur la base de données SMS d'Android
    cmd = [
        "shell", "content", "query", "--uri", "content://sms/inbox",
        "--projection", "address,body",
        "--sort", "date DESC", "--limit", str(count)
    ]
    res = _run_adb(cmd)
    if not res or "Row: 0" not in res:
        return "Aucun message trouvé ou permission refusée sur le tel."
    
    # Nettoyage sommaire du résultat
    messages = []
    for line in res.split('\n'):
        if "address=" in line:
            addr = re.search(r"address=([^,]+)", line)
            body = re.search(r"body=([^,]+)", line)
            if addr and body:
                messages.append(f"De {addr.group(1)} : {body.group(1)}")
    
    return "\n".join(messages) if messages else "Erreur de lecture des messages."

def send_sms(number: str, text: str) -> str:
    """Prépare et envoie un SMS (ouvre le compositeur sur le tel)."""
    try:
        # Utilisation de l'intent Android pour ouvrir le SMS avec le texte prêt
        cmd = [
            "shell", "am", "start", "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{number}", "--es", "sms_body", text, "--ez", "exit_on_sent", "true"
        ]
        _run_adb(cmd)
        return f"Compositeur SMS ouvert pour {number}. Appuyez sur Envoyer sur votre tel."
    except Exception as e:
        return f"Erreur d'envoi : {str(e)}"

def start_call(number: str) -> str:
    """Déclenche un appel vers un numéro spécifique."""
    res = _run_adb(["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{number}"])
    if "Error" in res:
        return f"Impossible de lancer l'appel : {res}"
    return f"Appel vers {number} lancé sur votre téléphone."

def get_phone_status() -> str:
    """Récupère le niveau de batterie du téléphone."""
    res = _run_adb(["shell", "dumpsys", "battery"])
    level = re.search(r"level: (\d+)", res)
    if level:
        return f"Batterie du téléphone : {level.group(1)}%."
    return "Impossible de récupérer le statut du téléphone."

# ── Registre des Outils ADB ──────────────────────────────────────────────
TOOLS_REGISTRY = {
    'connect_phone': connect_phone,
    'list_phone_files': list_phone_files,
    'read_last_sms': read_last_sms,
    'send_sms': send_sms,
    'start_call': start_call,
    'get_phone_status': get_phone_status
}

TOOLS_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'connect_phone',
            'description': 'Connecte le téléphone via Wireless ADB IP:PORT',
            'parameters': {
                'type': 'object',
                'properties': {
                    'address': {'type': 'string', 'description': 'IP et port (ex: 192.168.1.50:5555)'}
                },
                'required': ['address']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_last_sms',
            'description': 'Lit les derniers SMS reçus sur le téléphone',
            'parameters': {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'description': 'Nombre de messages à lire'}
                }
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'start_call',
            'description': 'Déclenche un appel sortant vers un numéro',
            'parameters': {
                'type': 'object',
                'properties': {
                    'number': {'type': 'string', 'description': 'Numéro de téléphone'}
                },
                'required': ['number']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_sms',
            'description': 'Envoie un SMS à un contact',
            'parameters': {
                'type': 'object',
                'properties': {
                    'number': {'type': 'string', 'description': 'Numéro de téléphone'},
                    'text': {'type': 'string', 'description': 'Contenu du message'}
                },
                'required': ['number', 'text']
            }
        }
    }
]
