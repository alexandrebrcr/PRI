#!/bin/bash

SOUND_CARD_IDX=2 # Carte son USB (aplay -l pour vérifier)

# Vérifier si pico2wave est installé (sudo apt install libttspico-utils)
if [ -x "$(command -v pico2wave)" ]; then
    # Création d'un fichier temporaire UNIQUE pour éviter les conflits au démarrage
    # $$ est le PID du processus shell actuel, $RANDOM ajoute de l'aléatoire
    TEMP_WAV="/dev/shm/tts_output_$$.$RANDOM.wav"
    
    # 1. Génération du fichier audio
    pico2wave -w "$TEMP_WAV" -l fr-FR "$@"
    
    # 2. Lecture du fichier
    aplay -D plughw:$SOUND_CARD_IDX,0 "$TEMP_WAV" 2>/dev/null
    
    # 3. Nettoyage
    rm -f "$TEMP_WAV"

else
    # Fallback sur Espeak (voix robotique) si Pico n'est pas là
    if ! [ -x "$(command -v espeak)" ]; then
        echo 'Erreur : ni pico2wave ni espeak installés.' >&2
        exit 1
    fi
    espeak -s 160 -v fr "$@" --stdout | aplay -D plughw:$SOUND_CARD_IDX,0 2>/dev/null
fi
