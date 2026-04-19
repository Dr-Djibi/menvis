import subprocess
import datetime
import os
import psutil

# --- HYPRLAND COMPÉTENCES ---

def open_application(app_name: str) -> str:
    """Ouvre une application (ex: firefox, alacritty, thunar) sur Hyprland."""
    app_name = app_name.lower().strip()
    try:
        subprocess.run(["hyprctl", "dispatch", "exec", app_name], check=True, capture_output=True)
        return f"L'application {app_name} a bien été lancée."
    except Exception as e:
        return f"Erreur lors de l'ouverture de {app_name} : {str(e)}"

def close_active_window() -> str:
    """Ferme la fenêtre active courante sur Hyprland."""
    try:
        subprocess.run(["hyprctl", "dispatch", "killactive"], check=True, capture_output=True)
        return "La fenêtre active a été fermée."
    except Exception as e:
        return f"Erreur de fermeture : {str(e)}"


# --- COMPÉTENCES SYSTÈME (Volume, Date, OS) ---

def get_current_time() -> str:
    """Récupère l'heure et la date courantes."""
    now = datetime.datetime.now()
    return now.strftime("Aujourd'hui, nous sommes le %d/%m/%Y et il est %H:%M.")

def set_volume(level: str) -> str:
    """Modifie le volume du système (0 à 100)."""
    try:
        level = level.replace('%', '').strip()
        # wpctl est souvent le standard moderne sous les distros récentes (Pipewire)
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{int(level)}%"], check=True)
        return f"Le volume a été réglé à {level}%."
    except Exception:
        # Fallback si wpctl n'existe pas, on tente via pamixer ou amixer
        try:
            subprocess.run(["pamixer", "--set-volume", str(level)], check=True)
            return f"Le volume a été réglé à {level}% via pamixer."
        except Exception as e:
            return f"Impossible de modifier le volume : {str(e)}"

def get_system_status() -> str:
    """Récupère l'état du système (RAM, CPU)."""
    cpu_usage = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    ram_total = round(ram.total / (1024**3), 1)
    return f"Processeur: {cpu_usage}% d'utilisation. Mémoire Vive: {ram_usage}% ({ram_total} Go au total)."

def get_weather(city: str) -> str:
    """Récupère la météo basique d'une ville (Text brut)."""
    try:
        result = subprocess.run(["curl", "-s", f"wttr.in/{city}?format=3"], capture_output=True, text=True, timeout=5)
        weather = result.stdout.strip()
        if weather:
             return f"La météo pour {city} est : {weather}"
        return "Impossible de récupérer la météo."
    except Exception as e:
        return f"Erreur réseau pour la météo: {str(e)}"


# --- EXPORT DES OUTILS ---
# Cela facilite l'intégration dans notre système LLM

TOOLS_REGISTRY = {
    'get_current_time': get_current_time,
    'open_application': open_application,
    'close_active_window': close_active_window,
    'set_volume': set_volume,
    'get_system_status': get_system_status,
    'get_weather': get_weather
}

# Définition JSON Schema des outils pour Ollama
TOOLS_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_current_time',
            'description': 'Donne la date et l\'heure actuelle de l\'ordinateur',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_application',
            'description': 'Ouvre un logiciel/application spécifique (ex: firefox, discord, kitty)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {'type': 'string', 'description': 'le nom raccourci de l\'application'}
                },
                'required': ['app_name']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'close_active_window',
            'description': 'Ferme la fenêtre immédiatement active affichée à l\'écran de l\'utilisateur.',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'set_volume',
            'description': 'Modifie le volume audio principal du système',
            'parameters': {
                'type': 'object',
                'properties': {
                    'level': {'type': 'string', 'description': 'Niveau du volume entre 0 et 100'}
                },
                'required': ['level']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_system_status',
            'description': 'Donne l\'état de la consommation de la RAM et du CPU',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': 'Consulte la météo locale',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': 'le nom de la ville ou du pays (ex: Paris, Tokyo)'}
                },
                'required': ['city']
            }
        }
    }
]
