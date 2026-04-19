#!/bin/bash
# install.sh - Installe Menvis comme un Daemon Natif Systemd

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="menvis-notif.service"

if [ "$1" == "--update" ] || [ "$1" == "update" ]; then
    echo "========================================="
    echo "🔄 TÉLÉCHARGEMENT DE LA NOUVELLE CONSCIENCE..."
    echo "========================================="
    cd "$DIR"
    git pull origin main
    source .venv/bin/activate
    pip install -r requirements.txt
    systemctl --user restart "$SERVICE_NAME"
    echo "✅ Mise à jour terminée avec succès."
    exit 0
fi

echo "========================================="
echo "🦾 INSTALLATION DE MENVIS V4 (DAEMON) 🦾"
echo "========================================="

# 1. Création du binaire global
echo "[1] Création de la commande globale 'menvis'..."
mkdir -p "$BIN_DIR"
cat << 'EOF' > "$BIN_DIR/menvis"
#!/bin/bash
# Exécution du cerveau
cd "$(dirname "$(readlink -f "$0")")/../menvis" || cd "$HOME/menvis"
source .venv/bin/activate
python main.py "$@"
EOF

chmod +x "$BIN_DIR/menvis"

# 2. Configuration Systemd pour le Listener D-Bus
echo "[2] Configuration du service d'écoute des Notifications (Systemd)..."
mkdir -p "$SYSTEMD_DIR"
cat << EOF > "$SYSTEMD_DIR/$SERVICE_NAME"
[Unit]
Description=Menvis Notification Listener (D-Bus Sixth Sense)
After=graphical-session.target

[Service]
Type=simple
ExecStart=$DIR/.venv/bin/python $DIR/daemon/notif_listener.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 3. Activation du Démon
echo "[3] Activation du Démon..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "========================================="
echo "✅ Menvis est maintenant ancré dans votre système !"
echo ""
echo "👉 DÈS MAINTENANT :"
echo "1. Tapez simplement 'menvis' depuis n'importe quel terminal pour lui parler."
echo "2. Hyprland UI : Ajoutez ces lignes dans votre ~/.config/hypr/hyprland.conf :"
echo "   windowrule = float, title:^(MenvisBubble)$"
echo "   windowrule = noborder, title:^(MenvisBubble)$"
echo "   windowrule = pin, title:^(MenvisBubble)$"
echo "   windowrule = move 100%-w-20 20, title:^(MenvisBubble)$"
echo "========================================="
