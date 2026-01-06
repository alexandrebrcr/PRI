#!/bin/bash

# Définition du dossier du projet (A ADAPTER selon votre vrai chemin sur la Jetson)
PROJECT_DIR="/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code"

# Attente pour être sûr que le système est bien chargé (Réseau, HW)
sleep 10

# Donne les permissions nécessaires au port série (Ultrasons)
if [ -e /dev/ttyTHS1 ]; then
    sudo chmod 666 /dev/ttyTHS1
fi

# Donne les droits d'exécution au script de parole
chmod +x "$PROJECT_DIR/text_to_speech.sh"

# Se place dans le dossier
cd "$PROJECT_DIR" || exit 1

# Lance le programme principal avec Python 3
# La sortie est redirigée vers un fichier de log pour le débogage
python main.py > logs_canne.txt 2>&1
