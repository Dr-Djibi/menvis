import subprocess
import os

def upgrade_self() -> str:
    """Utilise Github pour mettre à jour Menvis vers la dernière version connue."""
    try:
        install_script = "/home/menma/menvis/install.sh"
        if not os.path.exists(install_script):
            return "Le script d'installation système est introuvable."
            
        # Lance la mise à jour sans bloquer (sinon ça va freezer le main.py en attendant pip)
        subprocess.Popen(["bash", install_script, "--update"], cwd="/home/menma/menvis")
        return "Exécution de la procédure de mise à jour de mon code source via GitHub. Le système de fond sera relancé d'ici quelques instants !"
    except Exception as e:
        return f"Échec de l'auto-mise à jour : {e}"

def initiate_matrix_hack() -> str:
    """Action très visuelle : Ouvre un terminal Matrix stylé pour l'immersion J.A.R.V.I.S."""
    try:
        # Essaye kitty ou alacritty typiques sous Hyprland.
        # Fallback classique si cmatrix installé.
        term_cmd = ["kitty", "-e", "bash", "-c", "echo 'Connexion au serveur du Pentagone...' && sleep 1 && cmatrix || htop"]
        subprocess.Popen(term_cmd)
        return "Interface de piratage tactique lancée, Chef."
    except Exception:
         return "Impossible de lancer le mode hack (essayez d'installer 'kitty' et 'cmatrix')."

def upgrade_linux() -> str:
    """Ouvre un terminal dédié pour faire la mise à jour générale de Arch Linux (yay -Syu)."""
    try:
        subprocess.Popen(["kitty", "-e", "bash", "-c", "yay -Syu; echo ''; read -p 'Appuyez sur Entrée pour fermer...'"])
        return "J'ai ouvert un terminal sécurisé pour mettre à jour votre système d'exploitation EndeavourOS. Vous devrez peut-être entrer votre mot de passe."
    except Exception:
        return "Je ne trouve pas de moyen d'ouvrir le terminal de mise à jour système."

COOL_TOOLS = {
    'upgrade_self': upgrade_self,
    'initiate_matrix_hack': initiate_matrix_hack,
    'upgrade_linux': upgrade_linux
}

COOL_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'upgrade_self',
            'description': 'Mets à jour le code source de Menvis (toi-même) en téléchargeant les derniers changements sur GitHub (git pull) et en relançant ton service.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'initiate_matrix_hack',
            'description': 'Fais apparaître un terminal Matrix d\'apparence futuriste sur l\'écran de l\'utilisateur.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'upgrade_linux',
            'description': 'Lance la procédure de mise à jour globale de EndeavourOS / Linux (yay -Syu).',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    }
]
