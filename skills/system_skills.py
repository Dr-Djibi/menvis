import subprocess
import datetime
import os
import psutil
import requests
import re
from config import Config

# ── Fonctions Utilitaires ──────────────────────────────────────────────────
def get_current_time() -> str:
    """Retourne l'heure actuelle au format lisible."""
    return f"Il est actuellement {datetime.datetime.now().strftime('%H:%M')}."

def _find_desktop_exec(app_name: str) -> str:
    """Recherche la commande Exec dans les fichiers .desktop pour un nom donné."""
    search_paths = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications"
    ]
    
    app_name_lower = app_name.lower()
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
        for filename in os.listdir(path):
            if filename.endswith(".desktop"):
                filepath = os.path.join(path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Cherche Name=... (insensible à la casse)
                        name_match = re.search(r'^Name=(.*)$', content, re.IGNORECASE | re.MULTILINE)
                        if name_match and app_name_lower in name_match.group(1).lower():
                            # Trouve la ligne Exec
                            exec_match = re.search(r'^Exec=(.*)$', content, re.MULTILINE)
                            if exec_match:
                                cmd = exec_match.group(1)
                                # Nettoie les placeholders %u, %U, etc.
                                cmd = re.sub(r' %[a-zA-Z]', '', cmd).strip()
                                return cmd
                except Exception:
                    continue
    return None

def open_application(app_name: str) -> str:
    """Lance une application par son nom de commande ou son nom d'affichage (PWA)."""
    # 1. Tente de trouver un fichier .desktop d'abord (pour les PWAs et noms conviviaux)
    cmd = _find_desktop_exec(app_name)
    
    # 2. Si pas de .desktop, utilise le nom brut
    final_cmd = cmd if cmd else app_name
    
    try:
        subprocess.Popen(final_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"L'application {app_name} a été lancée."
    except Exception as e:
        return f"Erreur de lancement pour {app_name} : {str(e)}"

def open_folder(path: str) -> str:
    """Ouvre un dossier spécifique dans l'explorateur de fichiers Nautilus."""
    try:
        # Forcer Nautilus avec chemin absolu
        abs_path = os.path.abspath(os.path.expanduser(path))
        subprocess.run(["nautilus", abs_path], check=True)
        return f"Le dossier {path} est maintenant ouvert dans Nautilus."
    except Exception as e:
        return f"Erreur lors de l'ouverture du dossier : {str(e)}"

def switch_workspace(target_id: str) -> str:
    """Change l'espace de travail (workspace) actuel sur Hyprland."""
    try:
        # Test de charge RAM (Survival Mode)
        mem = psutil.virtual_memory().percent
        if Config.DEBUG:
            print(f"  [RAM] Avant switch: {mem}%")
            
        subprocess.run(["hyprctl", "dispatch", "workspace", str(target_id)], check=True)
        return f"Passage sur le workspace {target_id}."
    except Exception as e:
        return f"Erreur de changement d'espace : {str(e)}"

def move_window_to_workspace(target_id: str) -> str:
    """Déplace la fenêtre active vers un autre espace de travail."""
    try:
        subprocess.run(["hyprctl", "dispatch", "movetoworkspace", str(target_id)], check=True)
        return f"Fenêtre déplacée sur le workspace {target_id}."
    except Exception as e:
        return f"Erreur de déplacement : {str(e)}"

def open_on_workspace(app_name: str, target_id: str) -> str:
    """Lance une application (ou PWA) directement sur un workspace spécifique."""
    # 1. Cherche la commande via .desktop
    cmd = _find_desktop_exec(app_name)
    final_cmd = cmd if cmd else app_name
    
    try:
        # Syntaxe Hyprland : hyprctl dispatch exec [workspace ID] command
        subprocess.run(["hyprctl", "dispatch", "exec", f"[workspace {target_id}] {final_cmd}"], check=True)
        return f"Lancement de {app_name} sur le workspace {target_id}."
    except Exception as e:
        return f"Erreur de lancement ciblé : {str(e)}"

def close_active_window() -> str:
    """Ferme la fenêtre active courante sur Hyprland."""
    try:
        subprocess.run(["hyprctl", "dispatch", "killactive"], check=True)
        return "Fenêtre fermée."
    except Exception as e:
        return f"Erreur : {str(e)}"

def set_volume(level: int) -> str:
    """Règle le volume système (0-100) via pamixer."""
    try:
        subprocess.run(["pamixer", "--set-volume", str(level)], check=True)
        return f"Volume réglé à {level}%."
    except Exception as e:
        return f"Erreur volume : {str(e)}"

def get_system_status() -> str:
    """Récupère la charge CPU et la mémoire libre."""
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    return f"CPU: {cpu}%, RAM: {mem}%."

def get_weather(city: str = "Paris") -> str:
    """Récupère la météo actuelle pour une ville donnée."""
    try:
        r = requests.get(f"https://wttr.in/{city}?format=%C+%t")
        return f"Météo à {city} : {r.text}"
    except Exception:
        return "Impossible de récupérer la météo."

# ── Registre des Outils ──────────────────────────────────────────────────
TOOLS_REGISTRY = {
    'get_current_time': get_current_time,
    'open_application': open_application,
    'open_folder': open_folder,
    'switch_workspace': switch_workspace,
    'move_window_to_workspace': move_window_to_workspace,
    'open_on_workspace': open_on_workspace,
    'close_active_window': close_active_window,
    'set_volume': set_volume,
    'get_system_status': get_system_status,
    'get_weather': get_weather
}

TOOLS_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_current_time',
            'description': 'Obtenir l\'heure actuelle',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_application',
            'description': 'Lance une application par son nom (ex: Code, Spotify, Firefox)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {'type': 'string', 'description': 'Le nom de l\'application à lancer'}
                },
                'required': ['app_name']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_folder',
            'description': 'Ouvre un dossier spécifique dans Nautilus',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Le chemin absolu du dossier'}
                },
                'required': ['path']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'switch_workspace',
            'description': 'Change d\'espace de travail Hyprland (1-10)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'target_id': {'type': 'string', 'description': 'L\'ID du workspace'}
                },
                'required': ['target_id']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_on_workspace',
            'description': 'Lance une application (PWA incluse) sur un workspace spécifique',
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {'type': 'string', 'description': 'Nom de l\'application'},
                    'target_id': {'type': 'string', 'description': 'ID du workspace'}
                },
                'required': ['app_name', 'target_id']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_system_status',
            'description': 'Récupère la charge CPU et la mémoire vive (RAM) disponible.',
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'close_active_window',
            'description': 'Ferme la fenêtre actuellement active.',
            'parameters': {'type': 'object', 'properties': {}}
        }
    }
]
