#!/bin/bash

# === SCRIPT DE DEMARRAGE ===

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
