#!/bin/bash

# === SCRIPT DE DEMARRAGE ===

# 1. Attente active de la carte son (Max 15s)
count=0
while ! grep -q "usb" /proc/asound/modules && [ $count -lt 15 ]; do
  sleep 1
  count=$((count+1))
done
sleep 2 # Petite pause sécurité pour PulseAudio/ALSA

# 2. Annonce vocale de démarrage
if [ -x "$(command -v pico2wave)" ]; then
    pico2wave -w /dev/shm/sys_boot.wav -l fr-FR "Démarrage système. Initialisation en cours."
    timeout 5s aplay -D plughw:2,0 /dev/shm/sys_boot.wav >/dev/null 2>&1
    rm -f /dev/shm/sys_boot.wav
fi

# 3. Configuration du projet
PROJECT_DIR="/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code"

# Permissions port série (Ultrasons)
if [ -e /dev/ttyTHS1 ]; then
    sudo chmod 666 /dev/ttyTHS1
fi

cd "$PROJECT_DIR" || exit 1

# Droits d'exécution
chmod +x text_to_speech.sh

# 4. Lancement du programme PRINCIPAL
python3 -u main.py > logs_canne.txt 2>&1
