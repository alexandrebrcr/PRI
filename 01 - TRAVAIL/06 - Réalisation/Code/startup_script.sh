#!/bin/bash

# Annonce immédiate du démarrage (le plus tôt possible)
# Carte son 2 (USB)
if [ -x "$(command -v pico2wave)" ]; then
    pico2wave -w /dev/shm/sys_boot.wav -l fr-FR "Démarrage du système"
    aplay -D plughw:2,0 /dev/shm/sys_boot.wav 2>/dev/null
    rm -f /dev/shm/sys_boot.wav
fi

# Définition du dossier du projet
PROJECT_DIR="/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code"

sleep 3

# Donne les permissions nécessaires au port série (Ultrasons)
if [ -e /dev/ttyTHS1 ]; then
    sudo chmod 666 /dev/ttyTHS1
fi

# Donne les droits d'exécution au script de parole
chmod +x "$PROJECT_DIR/text_to_speech.sh"

# Se place dans le dossier
cd "$PROJECT_DIR" || exit 1

# Lance le programme principal avec Python 3
python main.py > logs_canne.txt 2>&1
