import subprocess
import os
import time
import threading
import shutil
from datetime import datetime

# ════════════════════════════════════════════════
#  📸  SCREENSHOT
# ════════════════════════════════════════════════

def take_screenshot(filename: str = "") -> str:
    """Prend une capture d'écran et l'enregistre dans ~/Images/Screenshots/."""
    screenshots_dir = os.path.expanduser("~/Images/Screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    if not filename:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(screenshots_dir, filename if filename.endswith(".png") else filename + ".png")
    tool = "grim" if shutil.which("grim") else "scrot"
    try:
        subprocess.run([tool, filepath], check=True, timeout=10)
        return f"📸 Capture d'écran enregistrée : {filepath}"
    except FileNotFoundError:
        return "Outil de capture introuvable. Installez grim : sudo pacman -S grim"
    except Exception as e:
        return f"Erreur capture d'écran : {e}"


# ════════════════════════════════════════════════
#  📋  PRESSE-PAPIER
# ════════════════════════════════════════════════

def read_clipboard() -> str:
    """Lit le contenu actuel du presse-papier (Wayland)."""
    try:
        result = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=5)
        content = result.stdout.strip()
        return f"Contenu du presse-papier : « {content} »" if content else "Le presse-papier est vide."
    except FileNotFoundError:
        return "wl-paste introuvable. Installez wl-clipboard : sudo pacman -S wl-clipboard"
    except Exception as e:
        return f"Erreur lecture presse-papier : {e}"


def write_clipboard(text: str) -> str:
    """Copie un texte dans le presse-papier (Wayland)."""
    try:
        proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        proc.communicate(input=text.encode())
        return f"✅ Copié dans le presse-papier : « {text} »"
    except FileNotFoundError:
        return "wl-copy introuvable. Installez wl-clipboard : sudo pacman -S wl-clipboard"
    except Exception as e:
        return f"Erreur écriture presse-papier : {e}"


# ════════════════════════════════════════════════
#  ⏱️  MINUTEUR / COMPTE À REBOURS
# ════════════════════════════════════════════════

def set_timer(seconds: int, label: str = "Minuteur") -> str:
    """Démarre un minuteur silencieux et envoie une notification sonore à la fin."""
    if seconds <= 0:
        return "La durée du minuteur doit être positive."

    def _timer_thread():
        time.sleep(seconds)
        subprocess.run(["notify-send", "-u", "critical", f"⏰ {label}", f"Temps écoulé ! ({seconds}s)"], timeout=5)
        subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    threading.Thread(target=_timer_thread, daemon=True).start()
    mins, secs = divmod(seconds, 60)
    duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"
    return f"⏱️ Minuteur « {label} » lancé pour {duration_str}. Je vous alerterai quand c'est fini !"


# ════════════════════════════════════════════════
#  🔒  VERROUILLAGE D'ÉCRAN
# ════════════════════════════════════════════════

def lock_screen() -> str:
    """Verrouille immédiatement l'écran (session Hyprland)."""
    for cmd in [["hyprlock"], ["swaylock"], ["loginctl", "lock-session"]]:
        if shutil.which(cmd[0]):
            subprocess.Popen(cmd)
            return "🔒 Écran verrouillé. À bientôt."
    return "Aucun gestionnaire de verrouillage trouvé (hyprlock, swaylock). Installez-en un."


# ════════════════════════════════════════════════
#  📝  NOTES RAPIDES (Nom & Extension au choix)
# ════════════════════════════════════════════════

NOTES_DIR = os.path.expanduser("~/Documents/MenvisNotes")

def save_quick_note(note: str, filename: str = "", extension: str = "md") -> str:
    """Sauvegarde une note dans un fichier dont vous choisissez le nom et l'extension."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    if not filename:
        filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ext = extension.lstrip(".") or "md"
    filepath = os.path.join(NOTES_DIR, f"{filename}.{ext}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"# Note du {timestamp}\n\n{note}\n" if ext == "md" else f"[{timestamp}]\n{note}\n"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Note enregistrée dans {filepath}"


def read_notes(filename: str = "") -> str:
    """Liste vos fichiers de notes, ou lit le contenu d'un fichier spécifique."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    if not filename:
        files = sorted(os.listdir(NOTES_DIR))
        if not files:
            return "Aucune note enregistrée pour l'instant."
        return "📂 Vos fichiers de notes :\n" + "\n".join(f"  - {f}" for f in files)
    matches = [f for f in os.listdir(NOTES_DIR) if f.startswith(filename)]
    if not matches:
        return f"Aucun fichier de note correspondant à '{filename}'."
    filepath = os.path.join(NOTES_DIR, matches[0])
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return f"Contenu de {matches[0]} :\n{content[-2000:]}"


# ════════════════════════════════════════════════
#  🚀  LANCEMENT D'APPLICATION (Auto-Détection)
# ════════════════════════════════════════════════

def _parse_desktop_file(filepath: str) -> dict:
    """Lit un fichier .desktop et retourne ses champs utiles."""
    data = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                for key in ("Name=", "Exec=", "Keywords=", "Comment="):
                    if line.startswith(key):
                        data[key[:-1]] = line.split("=", 1)[1].strip()
    except Exception:
        pass
    return data

def launch_app(app_name: str) -> str:
    """Détecte et lance automatiquement n'importe quelle app installée : native, PWA Firefox, etc."""
    name_lower = app_name.lower().strip()

    # ── Scan automatique de TOUS les .desktop (PWA + apps système) ──────────
    desktop_dirs = [
        os.path.expanduser("~/.local/share/applications/"),  # PWA Firefox + apps user
        "/usr/share/applications/",
        "/usr/local/share/applications/",
    ]

    best_match = None  # (score, filepath, display_name)

    for d in desktop_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".desktop"):
                continue
            fpath = os.path.join(d, fname)
            info = _parse_desktop_file(fpath)
            app_display = info.get("Name", "").lower()
            keywords    = info.get("Keywords", "").lower()
            comment     = info.get("Comment", "").lower()
            fname_lower = fname.lower()

            # Calcul du score de correspondance (plus c'est haut, mieux c'est)
            if name_lower == app_display or name_lower == fname_lower.replace(".desktop", ""):
                score = 4
            elif name_lower in fname_lower:
                score = 3
            elif name_lower in app_display or name_lower in keywords:
                score = 2
            elif name_lower in comment:
                score = 1
            else:
                continue

            if best_match is None or score > best_match[0]:
                best_match = (score, fpath, info.get("Name", fname))

    if best_match:
        _, fpath, display_name = best_match
        try:
            # gtk-launch prend le nom du fichier sans l'extension
            desktop_id = os.path.basename(fpath).replace(".desktop", "")
            subprocess.Popen(["gtk-launch", desktop_id],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"🚀 Lancement de {display_name}..."
        except Exception:
            pass

    # ── Fallback 1 : commande directe dans le PATH ───────────────────────────
    if shutil.which(name_lower):
        subprocess.Popen([name_lower], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"🚀 Lancement de {app_name} en cours..."

    # ── Fallback 2 : ouvrir le site web correspondant ────────────────────────
    subprocess.Popen(["xdg-open", f"https://{name_lower}.com"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"🌐 Application '{app_name}' introuvable localement. J'ai ouvert {app_name}.com dans Firefox."


# ════════════════════════════════════════════════
#  🌐  INFORMATIONS RÉSEAU
# ════════════════════════════════════════════════

def get_network_info() -> str:
    """Affiche les infos réseau : IP locale, interface active et état de la connexion Internet."""
    try:
        result = subprocess.run(["ip", "route", "get", "1.1.1.1"], capture_output=True, text=True, timeout=5)
        parts = result.stdout.split()
        src_idx = parts.index("src") if "src" in parts else -1
        dev_idx = parts.index("dev") if "dev" in parts else -1
        ip    = parts[src_idx + 1] if src_idx != -1 else "inconnue"
        iface = parts[dev_idx + 1] if dev_idx != -1 else "inconnue"
        ping  = subprocess.run(["ping", "-c", "1", "-W", "2", "1.1.1.1"], capture_output=True, timeout=5)
        internet = "✅ Connecté à Internet" if ping.returncode == 0 else "❌ Pas d'accès Internet"
        return f"🌐 Réseau :\n- Interface : {iface}\n- IP Locale : {ip}\n- {internet}"
    except Exception as e:
        return f"Erreur récupération réseau : {e}"


# ════════════════════════════════════════════════
#  🗑️  VIDER LA CORBEILLE
# ════════════════════════════════════════════════

def empty_trash() -> str:
    """Vide définitivement la corbeille de l'utilisateur."""
    trash_dir = os.path.expanduser("~/.local/share/Trash/files/")
    if not os.path.exists(trash_dir) or not os.listdir(trash_dir):
        return "La corbeille est déjà vide."
    try:
        subprocess.run(["gio", "trash", "--empty"], check=True, timeout=10)
        return "🗑️ Corbeille vidée définitivement."
    except Exception:
        import shutil as sh
        sh.rmtree(trash_dir, ignore_errors=True)
        os.makedirs(trash_dir, exist_ok=True)
        return "🗑️ Corbeille vidée (méthode directe)."


# ════════════════════════════════════════════════
#  🗺️  REGISTRES D'EXPORT
# ════════════════════════════════════════════════

EXTRA_TOOLS = {
    'take_screenshot':  take_screenshot,
    'read_clipboard':   read_clipboard,
    'write_clipboard':  write_clipboard,
    'set_timer':        set_timer,
    'lock_screen':      lock_screen,
    'save_quick_note':  save_quick_note,
    'read_notes':       read_notes,
    'launch_app':       launch_app,
    'get_network_info': get_network_info,
    'empty_trash':      empty_trash,
}

EXTRA_SCHEMAS = [
    {
        'type': 'function', 'function': {
            'name': 'take_screenshot',
            'description': "Prend une capture d'écran complète et l'enregistre dans ~/Images/Screenshots/.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string', 'description': "Nom optionnel du fichier (sans extension). Laissez vide pour un nom automatique avec la date."}
                },
                'required': []
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'read_clipboard',
            'description': "Lit et retourne ce qui est actuellement dans le presse-papier de l'utilisateur.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'write_clipboard',
            'description': "Copie un texte dans le presse-papier pour que l'utilisateur puisse le coller.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string', 'description': 'Le texte à copier dans le presse-papier'}
                },
                'required': ['text']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'set_timer',
            'description': "Lance un minuteur/compte à rebours et émet une alerte sonore + visuelle à la fin.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'seconds': {'type': 'integer', 'description': 'Durée en secondes (ex: 300 pour 5 minutes)'},
                    'label':   {'type': 'string',  'description': "Nom du minuteur (ex: 'Pizza au four')"}
                },
                'required': ['seconds']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'lock_screen',
            'description': "Verrouille immédiatement l'écran et la session Hyprland de l'utilisateur.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'save_quick_note',
            'description': "Enregistre une note dans un fichier dont l'utilisateur choisit le nom et l'extension (md, txt, py, json…).",
            'parameters': {
                'type': 'object',
                'properties': {
                    'note':      {'type': 'string', 'description': 'Le texte de la note à enregistrer'},
                    'filename':  {'type': 'string', 'description': "Nom du fichier sans extension (ex: 'idees_projet'). Laissez vide pour un nom auto."},
                    'extension': {'type': 'string', 'description': "Extension : 'md' (défaut), 'txt', 'py', 'json', etc."}
                },
                'required': ['note']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'read_notes',
            'description': "Liste les fichiers de notes disponibles, ou lit le contenu d'un fichier spécifique.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string', 'description': "Nom du fichier de note à lire (sans extension). Laissez vide pour voir tous les fichiers."}
                },
                'required': []
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'launch_app',
            'description': "Détecte et lance automatiquement n'importe quelle application : native, PWA Firefox (Spotify, WhatsApp, YouTube…), ou application système. Aucune liste nécessaire – détection intelligente.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {'type': 'string', 'description': "Nom de l'application (ex: 'spotify', 'terminal', 'discord', 'kdeconnect', 'firefox', 'gimp')"}
                },
                'required': ['app_name']
            }
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'get_network_info',
            'description': "Affiche l'IP locale, l'interface réseau active et vérifie la connexion Internet.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function', 'function': {
            'name': 'empty_trash',
            'description': "Vide définitivement la corbeille du système pour libérer de l'espace disque.",
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
]
