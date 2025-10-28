#!/bin/bash

#permission au port ths1

sleep 5

/bin/chmod 666 /dev/ttyTHS1

# lancer les codes
python /home/canneblancheintelligente/Documents/PRI_IRFAN/ultrasonic.py & ultrasonic_pid=$!

# attendre 5sec
sleep 4

#arret 

kill $ultrasonic_pid

#lancement du main

python /home/canneblancheintelligente/Documents/PRI_IRFAN/main.py
