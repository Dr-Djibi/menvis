import subprocess
import os
import shutil
from datetime import datetime

# ════════════════════════════════════════════════
#  🔍  RECHERCHE DE FICHIER INTELLIGENTE
# ════════════════════════════════════════════════

def find_file(name: str, search_path: str = "~") -> str:
    """Recherche un fichier ou dossier par son nom sur tout le système."""
    search_path = os.path.expanduser(search_path)
    tool = "fd" if shutil.which("fd") else "find"

    try:
        if tool == "fd":
            result = subprocess.run(
                ["fd", name, search_path, "--max-results", "10"],
                capture_output=True, text=True, timeout=15
            )
        else:
            result = subprocess.run(
                ["find", search_path, "-name", f"*{name}*", "-maxdepth", "8"],
                capture_output=True, text=True, timeout=15
            )

        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if not lines:
            return f"Aucun fichier correspondant à '{name}' trouvé dans {search_path}."
        return f"📂 Fichiers trouvés pour '{name}' :\n" + "\n".join(f"  {p}" for p in lines[:10])
    except Exception as e:
        return f"Erreur de recherche : {e}"


# ════════════════════════════════════════════════
#  💾  UTILISATION DU DISQUE
# ════════════════════════════════════════════════

def get_disk_usage() -> str:
    """Affiche l'espace disque utilisé par partition et les 5 dossiers les plus lourds."""
    try:
        df = subprocess.run(["df", "-h", "--output=target,size,used,avail,pcent"],
                            capture_output=True, text=True, timeout=5)
        lines = [l for l in df.stdout.splitlines() if l and not l.startswith("Filesystem")
                 and ("/" in l.split()[0])]
        disk_info = "\n".join(lines[:6])

        # Top 5 dossiers les plus lourds dans le home
        du = subprocess.run(
            ["du", "-sh", "--max-depth=1", os.path.expanduser("~")],
            capture_output=True, text=True, timeout=10
        )
        du_lines = sorted(
            [l for l in du.stdout.splitlines() if l],
            key=lambda x: x.split()[0], reverse=True
        )[:5]
        heavy = "\n".join(du_lines) if du_lines else "N/A"

        return f"💾 Disques :\n{disk_info}\n\n📁 Dossiers les + lourds dans ~/ :\n{heavy}"
    except Exception as e:
        return f"Erreur utilisation disque : {e}"


# ════════════════════════════════════════════════
#  ⚡  TUER UN PROCESSUS
# ════════════════════════════════════════════════

def kill_process(process_name: str) -> str:
    """Termine un processus par son nom (ex: 'firefox', 'code', 'vlc')."""
    try:
        result = subprocess.run(["pgrep", "-l", process_name], capture_output=True, text=True)
        if not result.stdout.strip():
            return f"Aucun processus '{process_name}' en cours d'exécution."

        subprocess.run(["pkill", "-f", process_name], timeout=5)
        return f"✅ Processus '{process_name}' terminé."
    except Exception as e:
        return f"Impossible de terminer '{process_name}' : {e}"


# ════════════════════════════════════════════════
#  📡  WIFI
# ════════════════════════════════════════════════

def list_wifi_networks() -> str:
    """Liste les réseaux Wi-Fi disponibles à proximité."""
    try:
        result = subprocess.run(
            ["nmcli", "-f", "SIGNAL,SSID,SECURITY", "device", "wifi", "list"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        return f"📡 Réseaux Wi-Fi disponibles :\n{output}" if output else "Aucun réseau détecté."
    except FileNotFoundError:
        return "nmcli introuvable. Installez NetworkManager."
    except Exception as e:
        return f"Erreur Wi-Fi : {e}"


def connect_wifi(ssid: str, password: str = "") -> str:
    """Se connecte à un réseau Wi-Fi par son nom (SSID)."""
    try:
        cmd = ["nmcli", "device", "wifi", "connect", ssid]
        if password:
            cmd += ["password", password]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            return f"✅ Connecté au réseau Wi-Fi '{ssid}' avec succès !"
        return f"Échec de connexion à '{ssid}' : {result.stderr.strip()}"
    except Exception as e:
        return f"Erreur de connexion Wi-Fi : {e}"


# ════════════════════════════════════════════════
#  📦  ARCHIVES (Compression / Extraction)
# ════════════════════════════════════════════════

def compress_files(source_path: str, output_name: str = "") -> str:
    """Compresse un fichier ou un dossier en archive .tar.gz."""
    source_path = os.path.expanduser(source_path)
    if not os.path.exists(source_path):
        return f"Chemin introuvable : {source_path}"
    if not output_name:
        output_name = os.path.basename(source_path) + f"_{datetime.now().strftime('%Y%m%d')}.tar.gz"
    if not output_name.endswith((".tar.gz", ".zip", ".tar")):
        output_name += ".tar.gz"
    
    output_path = os.path.join(os.path.dirname(source_path), output_name)
    try:
        subprocess.run(["tar", "-czf", output_path, "-C",
                        os.path.dirname(source_path), os.path.basename(source_path)],
                       check=True, timeout=60)
        return f"📦 Archive créée : {output_path}"
    except Exception as e:
        return f"Erreur de compression : {e}"


def extract_archive(archive_path: str, destination: str = "") -> str:
    """Extrait automatiquement une archive (.zip, .tar.gz, .7z, .rar…) dans un dossier."""
    archive_path = os.path.expanduser(archive_path)
    if not os.path.exists(archive_path):
        return f"Archive introuvable : {archive_path}"
    
    dest = os.path.expanduser(destination) if destination else os.path.dirname(archive_path)
    os.makedirs(dest, exist_ok=True)
    
    name = archive_path.lower()
    try:
        if name.endswith(".zip"):
            subprocess.run(["unzip", archive_path, "-d", dest], check=True, timeout=60)
        elif name.endswith((".tar.gz", ".tgz")):
            subprocess.run(["tar", "-xzf", archive_path, "-C", dest], check=True, timeout=60)
        elif name.endswith(".tar.bz2"):
            subprocess.run(["tar", "-xjf", archive_path, "-C", dest], check=True, timeout=60)
        elif name.endswith((".tar.xz", ".tar.zst")):
            subprocess.run(["tar", "-xf", archive_path, "-C", dest], check=True, timeout=60)
        elif name.endswith(".7z") and shutil.which("7z"):
            subprocess.run(["7z", "x", archive_path, f"-o{dest}"], check=True, timeout=60)
        elif name.endswith(".rar") and shutil.which("unrar"):
            subprocess.run(["unrar", "x", archive_path, dest], check=True, timeout=60)
        else:
            return f"Format d'archive non supporté ou outil manquant pour : {os.path.basename(archive_path)}"
        return f"📂 Archive extraite dans : {dest}"
    except Exception as e:
        return f"Erreur d'extraction : {e}"


# ════════════════════════════════════════════════
#  🔁  VÉRIFICATION DES MISES À JOUR SYSTÈME
# ════════════════════════════════════════════════

def check_system_updates() -> str:
    """Vérifie si des mises à jour sont disponibles pour EndeavourOS (sans installer)."""
    try:
        result = subprocess.run(
            ["checkupdates"],  # Outil officiel Arch Linux
            capture_output=True, text=True, timeout=30
        )
        updates = result.stdout.strip()
        if not updates:
            return "✅ Votre système est à jour. Aucune mise à jour disponible."
        count = len(updates.splitlines())
        return f"🔄 {count} mise(s) à jour disponible(s) :\n{updates[:1000]}"
    except FileNotFoundError:
        # Fallback yay
        try:
            result = subprocess.run(
                ["yay", "-Qu", "--aur"],
                capture_output=True, text=True, timeout=30
            )
            updates = result.stdout.strip()
            return f"🔄 Mises à jour AUR disponibles :\n{updates}" if updates else "✅ Tout est à jour."
        except Exception:
            return "Impossible de vérifier les mises à jour (checkupdates/yay non trouvé)."
    except Exception as e:
        return f"Erreur vérification mises à jour : {e}"


# ════════════════════════════════════════════════
#  🧮  CALCUL RAPIDE (via Python)
# ════════════════════════════════════════════════

def calculate(expression: str) -> str:
    """Évalue une expression mathématique (ex: '(15 * 8) + 42 / 2')."""
    # Sécurisé : on n'autorise que les caractères mathématiques
    allowed = set("0123456789+-*/().,% ")
    if not all(c in allowed for c in expression):
        return "Expression contenant des caractères non autorisés. Utilisez uniquement +, -, *, /, (, )."
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"🧮 {expression} = {result}"
    except Exception as e:
        return f"Erreur de calcul : {e}"


# ════════════════════════════════════════════════
#  🗺️  REGISTRES D'EXPORT
# ════════════════════════════════════════════════

SMART_TOOLS = {
    'find_file':           find_file,
    'get_disk_usage':      get_disk_usage,
    'kill_process':        kill_process,
    'list_wifi_networks':  list_wifi_networks,
    'connect_wifi':        connect_wifi,
    'compress_files':      compress_files,
    'extract_archive':     extract_archive,
    'check_system_updates': check_system_updates,
    'calculate':           calculate,
}

SMART_SCHEMAS = [
    {
        'type': 'function', 'function': {
            'name': 'find_file',
            'description': "Recherche intelligemment un fichier ou dossier par son nom sur le disque.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'name':        {'type': 'string', 'description': "Nom du fichier à rechercher (partial ok, ex: 'rapport', 'photo.jpg')"},
                    'search_path': {'type': 'string', 'description': "Dossier de départ (défaut: ~ home). Ex: '/home/menma/Documents'"}
                },
                'required': ['name']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'get_disk_usage',
            'description': "Affiche l'espace disque utilisé par partition et les dossiers les plus lourds dans le répertoire personnel.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'kill_process',
            'description': "Termine un processus actif par son nom (ex: arrêter Firefox qui freeze, tuer un jeu bloqué).",
            'parameters': {
                'type': 'object',
                'properties': {
                    'process_name': {'type': 'string', 'description': "Nom du processus à tuer (ex: 'firefox', 'vlc', 'code')"}
                },
                'required': ['process_name']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'set_wallpaper',
            'description': "Change le fond d'écran du bureau Hyprland avec une image depuis le disque.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'image_path': {'type': 'string', 'description': "Chemin absolu ou relatif de l'image (ex: '~/Images/fond.jpg')"}
                },
                'required': ['image_path']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'list_wifi_networks',
            'description': "Scanne et liste les réseaux Wi-Fi disponibles à proximité avec leur force de signal.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'connect_wifi',
            'description': "Connecte le PC à un réseau Wi-Fi spécifique par son nom (SSID).",
            'parameters': {
                'type': 'object',
                'properties': {
                    'ssid':     {'type': 'string', 'description': "Nom du réseau Wi-Fi (SSID)"},
                    'password': {'type': 'string', 'description': "Mot de passe (laisser vide si réseau ouvert ou déjà mémorisé)"}
                },
                'required': ['ssid']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'compress_files',
            'description': "Compresse un fichier ou dossier en archive .tar.gz pour sauvegarder ou partager.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'source_path': {'type': 'string', 'description': "Chemin du fichier ou dossier à compresser"},
                    'output_name': {'type': 'string', 'description': "Nom de l'archive à créer (optionnel, avec ou sans extension)"}
                },
                'required': ['source_path']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'extract_archive',
            'description': "Extrait automatiquement n'importe quelle archive (.zip, .tar.gz, .7z, .rar…) – détecte le format seul.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'archive_path': {'type': 'string', 'description': "Chemin de l'archive à extraire"},
                    'destination':  {'type': 'string', 'description': "Dossier de destination (optionnel – même dossier par défaut)"}
                },
                'required': ['archive_path']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'check_system_updates',
            'description': "Vérifie si des mises à jour sont disponibles pour EndeavourOS/Arch Linux sans les installer.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'calculate',
            'description': "Effectue un calcul mathématique rapide et retourne le résultat (addition, soustraction, multiplication, division, pourcentage…).",
            'parameters': {
                'type': 'object',
                'properties': {
                    'expression': {'type': 'string', 'description': "Expression à calculer (ex: '(15 * 8) + 42 / 2', '20 * 0.15')"}
                },
                'required': ['expression']
            }
        }
    },
]
