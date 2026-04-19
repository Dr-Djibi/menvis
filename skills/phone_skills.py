import subprocess
import json
import shutil

# ─────────────────────────────────────────────
#  UTILITAIRE INTERNE : Trouver l'ID du Device
# ─────────────────────────────────────────────

def _get_device_id() -> str | None:
    """Récupère automatiquement l'ID du premier appareil KDE Connect trouvé et connecté."""
    if not shutil.which("kdeconnect-cli"):
        return None
    try:
        result = subprocess.run(
            ["kdeconnect-cli", "--list-devices", "--id-only"],
            capture_output=True, text=True, timeout=5
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        return lines[0] if lines else None
    except Exception:
        return None

def _get_reachable_device_id() -> str | None:
    """Idem, mais uniquement les appareils joignables en ce moment (plus fiable)."""
    if not shutil.which("kdeconnect-cli"):
        return None
    try:
        result = subprocess.run(
            ["kdeconnect-cli", "--list-available", "--id-only"],
            capture_output=True, text=True, timeout=5
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        return lines[0] if lines else None
    except Exception:
        return None

# ─────────────────────────────────────────────
#  COMMANDES KDE CONNECT
# ─────────────────────────────────────────────

def ring_phone() -> str:
    """Fait sonner très fort le téléphone connecté via KDE Connect."""
    dev = _get_reachable_device_id()
    if not dev:
        return "Aucun appareil KDE Connect joignable. Vérifiez que votre téléphone est sur le même réseau Wi‑Fi et que KDE Connect est ouvert."
    try:
        subprocess.run(["kdeconnect-cli", "-d", dev, "--ring"], check=True, timeout=5)
        return "Votre téléphone sonne ! Bonne chance pour le retrouver. 🔔"
    except Exception as e:
        return f"KDE Connect a refusé la commande : {e}"


def ping_phone(message: str) -> str:
    """Envoie une notification texte sur le téléphone via KDE Connect."""
    dev = _get_reachable_device_id()
    if not dev:
        return "Aucun appareil KDE Connect joignable. Assurez‑vous d'être sur le même Wi‑Fi."
    try:
        subprocess.run(["kdeconnect-cli", "-d", dev, "--ping-msg", message], check=True, timeout=5)
        return f"Notification envoyée sur votre téléphone : « {message} »"
    except Exception as e:
        return f"Échec de l'envoi de la notification : {e}"


def send_sms(phone_number: str, message: str) -> str:
    """Envoie un SMS depuis votre téléphone Android via KDE Connect."""
    dev = _get_reachable_device_id()
    if not dev:
        return "Téléphone non joignable via KDE Connect."
    try:
        subprocess.run(
            ["kdeconnect-cli", "-d", dev, "--send-sms", message, "--destination", phone_number],
            check=True, timeout=10
        )
        return f"SMS envoyé au {phone_number} : « {message} »"
    except Exception as e:
        return f"Impossible d'envoyer le SMS : {e}"


def get_phone_battery() -> str:
    """Vérifie le niveau de batterie du téléphone Android connecté."""
    dev = _get_reachable_device_id()
    if not dev:
        return "Téléphone non joignable. KDE Connect n'est pas actif ou votre téléphone n'est pas sur le même réseau."
    try:
        result = subprocess.run(
            ["kdeconnect-cli", "-d", dev, "--battery"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.strip() or result.stderr.strip()
        return f"Batterie de votre téléphone : {output}" if output else "Impossible de récupérer le niveau de batterie."
    except Exception as e:
        return f"Erreur batterie KDE Connect : {e}"


def list_kdeconnect_devices() -> str:
    """Liste tous les appareils KDE Connect connus et indique lesquels sont actifs."""
    if not shutil.which("kdeconnect-cli"):
        return "La commande kdeconnect-cli est introuvable. Installez kdeconnect (yay -S kdeconnect)."
    try:
        result = subprocess.run(
            ["kdeconnect-cli", "--list-devices"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.strip()
        if not output:
            return "Aucun appareil KDE Connect détecté. Ouvrez l'application sur votre téléphone."
        return f"Appareils KDE Connect :\n{output}"
    except Exception as e:
        return f"Erreur lors de la liste des appareils : {e}"


def share_file_to_phone(file_path: str) -> str:
    """Envoie un fichier local de votre PC vers votre téléphone Android via KDE Connect."""
    import os
    if not os.path.exists(file_path):
        return f"Le fichier '{file_path}' est introuvable sur votre PC."
    dev = _get_reachable_device_id()
    if not dev:
        return "Téléphone non joignable via KDE Connect."
    try:
        subprocess.run(
            ["kdeconnect-cli", "-d", dev, "--share", file_path],
            check=True, timeout=15
        )
        return f"Fichier '{file_path}' envoyé avec succès sur votre téléphone !"
    except Exception as e:
        return f"Impossible de partager le fichier : {e}"


# ─────────────────────────────────────────────
#  REGISTRE
# ─────────────────────────────────────────────

PHONE_TOOLS = {
    'ring_phone': ring_phone,
    'ping_phone': ping_phone,
    'send_sms': send_sms,
    'get_phone_battery': get_phone_battery,
    'list_kdeconnect_devices': list_kdeconnect_devices,
    'share_file_to_phone': share_file_to_phone,
}

PHONE_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'ring_phone',
            'description': "Fait sonner très fort le téléphone portable de l'utilisateur via KDE Connect pour l'aider à le retrouver.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'ping_phone',
            'description': "Envoie une notification texte personnalisée sur le téléphone Android via KDE Connect.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': 'Le contenu de la notification à afficher sur le téléphone'}
                },
                'required': ['message']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_sms',
            'description': "Envoie un SMS depuis le téléphone Android de l'utilisateur via KDE Connect.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'phone_number': {'type': 'string', 'description': "Numéro de téléphone destinataire (ex: +33612345678)"},
                    'message': {'type': 'string', 'description': 'Le texte du SMS'}
                },
                'required': ['phone_number', 'message']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_phone_battery',
            'description': "Vérifie le niveau de batterie restant sur le téléphone Android connecté via KDE Connect.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_kdeconnect_devices',
            'description': "Liste tous les appareils appairés à KDE Connect et indique lesquels sont en ligne.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'share_file_to_phone',
            'description': "Envoie un fichier du PC vers le téléphone Android de l'utilisateur via KDE Connect.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'file_path': {'type': 'string', 'description': "Chemin absolu du fichier à envoyer (ex: /home/menma/photo.jpg)"}
                },
                'required': ['file_path']
            }
        }
    }
]
