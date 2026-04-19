# Menvis - Conscience Artificielle / Assistant Local (Style J.A.R.V.I.S)

Menvis est un assistant virtuel d'intelligence artificielle locale conçu spécifiquement pour les systèmes Linux, focalisé sur l'environnement **EndeavourOS / Hyprland**. 
Entièrement hors ligne, il utilise **Ollama** (`qwen2.5:1.5b`) et offre une interface vocale bidirectionnelle continue sans sollicitation textuelle.

## 🚀 Fonctionnalités
- **Écoute Continue & Synthèse Vocale :** Conversation 100% à la voix via `faster-whisper` (micro) et `edge-tts` (voix naturelle fluide).
- **Proactif & Mentorat :** La personnalité système de Menvis est celle d'un partenaire charismatique capable de donner des ordres.
- **Micro-UI Flottante (Hyprland) :** Affiche une bulle d'incantation visuelle ("Widget") superposée et borderless lors de la prise de parole, agissant en tant qu'interface physique sans dépendre d'un système lourd.
- **Daemon "Sixième Sens" (Notifications) :** Écoute passive de l'OS via `D-Bus` pour intercepter les notifications du système et du téléphone (KDE Connect).
- **Outils Système & Clavier Fantôme :** 
   - Pilote Hyprland (fermeture de fenêtres, lancements).
   - Simule des frappes réelles avec `wtype` (Wayland).
   - Gère le volume maître (`pamixer`, `wpctl`) et les médias (`playerctl` ciblant Firefox).
   - Moteur de Recherche en CLI, météo, statut CPU/RAM.
- **Tri de Fichiers Magique :** Range et organise de lui-même le chaos de vos dossiers (catégorisation automatique des exécutions, images, vidéos, docs).
- **Mémoire Persistante :** Base JSON pour retenir pour toujours vos traits ou préférences.

## 📦 Installation des dépendances Système (Arch Linux)
Vous aurez besoin des paquets suivants :
```bash
yay -S ollama alsa-utils pamixer wtype playerctl hyprland mako
```

## ⚙️ Intégration Visuelle (Hyprland)
Ajoutez ces règles à votre `~/.config/hypr/hyprland.conf` pour activer la bulle Menvis de manière élégante :
```conf
windowrule = float, title:^(MenvisBubble)$
windowrule = noborder, title:^(MenvisBubble)$
windowrule = pin, title:^(MenvisBubble)$
windowrule = move 100%-w-20 20, title:^(MenvisBubble)$
```

## 🔌 Déploiement Local (Service Systemd)
Pour une installation profonde (Daemon), exécutez simplement :
```bash
chmod +x install.sh
./install.sh
```
Cela fixera les chemins globaux et activera `menvis-notif.service` afin qu'il écoute vos événements silencieusement dès le boot.

## 🧠 Utilisation
- Commande globale : `menvis` (lance la boucle locale d'écoute vocale).
- Option terminal : `menvis "range mon dossier"` (interroge sans vocal).

> *Note: Pour arrêter la boucle vocale de Menvis, dites-lui simplement: "Menvis arrête-toi" ou "Désactiver".*
