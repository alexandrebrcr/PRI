#!/bin/bash

SOUND_CARD_IDX=2
# Réglages de la voix
SPEED="1.6"    # 1.0 = Normal
PITCH="-200"   # 0 = Normal

# Vérifier si pico2wave est installé
if [ -x "$(command -v pico2wave)" ]; then
    # Fichiers temporaires
    RAW_WAV="/dev/shm/tts_raw_$$.wav"
    FINAL_WAV="/dev/shm/tts_final_$$.wav"
    
    # 1. Génération du fichier brut avec Pico
    pico2wave -w "$RAW_WAV" -l fr-FR "$@"
    
    # 2. Traitement avec SoX (Vitesse + Tonalité)
    sox "$RAW_WAV" "$FINAL_WAV" tempo $SPEED pitch $PITCH 2>/dev/null
    
    # 3. Lecture du fichier traité
    aplay -D plughw:$SOUND_CARD_IDX,0 "$FINAL_WAV" 2>/dev/null
    
    # Nettoyage
    rm -f "$RAW_WAV" "$FINAL_WAV"

else
    # Fallback Espeak (lui a des options natives)
    espeak -s 160 -v fr "$@" --stdout | aplay -D plughw:$SOUND_CARD_IDX,0 2>/dev/null
fi