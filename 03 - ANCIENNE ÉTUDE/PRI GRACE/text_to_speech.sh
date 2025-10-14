#!/bin/bash

# Paramètres configurables via variables d'environnement
SOUND_CARD_IDX="${SOUND_CARD_IDX:-2}"
ESPEAK_VOICE="${ESPEAK_VOICE:-fr}"
ESPEAK_SPEED="${ESPEAK_SPEED:-160}"

# Vérification
if ! [ -x "$(command -v espeak)" ]; then
    echo 'Erreur : espeak non installé.' >&2
    exit 1
fi

# Générer le son
espeak -s "${ESPEAK_SPEED}" -v "${ESPEAK_VOICE}" "$@" --stdout | aplay -q -D "plughw:${SOUND_CARD_IDX},0"