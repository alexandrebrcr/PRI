#!/bin/bash

# Permission au port THS1
sleep 2
chmod 666 /dev/ttyTHS1

# Lancement direct du main (pas besoin de démarrer/tuer ultrasonic.py séparément)
python3 /home/canneblancheintelligente/Documents/PRI_IRFAN/main.py