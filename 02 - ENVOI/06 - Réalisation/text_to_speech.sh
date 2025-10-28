#!/bin/bash

SOUND_CARD_IDX=2 # Changer si nécessaire pour votre carte son

if ! [ -x "$(command -v espeak)" ]; then
	echo 'Erreur : easpeak non installé.' >&2
	exit 1
fi

# Générer un son avec espeak et le jouer avec aplay
espeak -s 160 -v fr "$@" --stdout | aplay -D plughw:$SOUND_CARD_IDX,0
