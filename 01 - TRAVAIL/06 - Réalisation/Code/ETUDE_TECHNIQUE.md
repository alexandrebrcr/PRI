# Étude technique – Système de canne intelligente (dossier « PRI IRFAN »)

Ce document présente le fonctionnement, l’architecture, les dépendances, les flux, les risques et des améliorations proposées pour l’application Python destinée à une canne intelligente basée sur NVIDIA Jetson Nano.

## 1) Objectif et finalité

- Finalité: assister la navigation d’une personne malvoyante en détectant l’environnement (objets, distances) et en restituant l’information par synthèse vocale (et potentiellement vibration).
- Plateforme: Jetson Nano sous Linux (GPIO, caméra CSI/USB, port série UART /dev/ttyTHS1, audio).
- Usage: deux modes de fonctionnement, commutables par un bouton poussoir.
  - Mode « exploration »: détecte les objets via la caméra et annonce leur nom + distance.
  - Mode « marche »: annonce la distance libre devant l’utilisateur selon des seuils.

## 2) Architecture logicielle (modules)

Répertoire: `PRI IRFAN/`

- `main.py`: orchestration. Initialise les composants (bouton, vibration, ultrason, caméra, TTS) et gère la boucle principale et les 2 modes.
- `bouton.py` (`Button`): lecture du bouton GPIO (pin BOARD 11) avec anti-rebond simple.
- `vibration.py` (`Vibration`): contrôle d’un vibreur sur GPIO (pin BOARD 13). Initialisé dans `main.py` mais non utilisé dans la logique.
- `ultrasonic.py` (`UltrasonicSensor`): lecture d’un capteur ultrason via UART `/dev/ttyTHS1` (9600 bauds). Décodage d’une trame 4 octets avec tête 0xFF et checksum, conversion en cm.
- `camera.py` (`Camera`): détection d’objets avec Jetson Inference (`detectNet`, modèle par défaut `ssd-mobilenet-v2`) sur un flux vidéo (`csi://0`). Fournit les détections et les libellés de classes.
- `sound.py` (`Sound`): synthèse vocale via le script shell `text_to_speech.sh` en appelant `espeak` → `aplay`.
- `text_to_speech.sh`: génère un flux audio avec `espeak` (voix fr) et le joue avec `aplay` sur la carte son indexée par `SOUND_CARD_IDX` (défaut: 2).
- `startup_script.sh`: script de démarrage (ex. pour systemd) donnant les permissions à `/dev/ttyTHS1`, lançant un test ultrason, puis `main.py`.

Remarque: unité systemd non fournie dans ce dossier (une version existe côté « PRI GRACE »), mais fortement recommandée pour un démarrage au boot.

## 3) Dépendances matérielles

- Jetson Nano avec GPIO activés (mode BOARD).
- Bouton poussoir sur pin physique 11 (entrée pull-down).
- Vibreur (sortie) sur pin physique 13.
- Capteur ultrason série (UART) connecté à `/dev/ttyTHS1`.
- Caméra CSI (URI `csi://0`) ou USB (`/dev/video0` si nécessaire).
- Sortie audio (carte ALSA), haut-parleur ou casque (index `SOUND_CARD_IDX`).

## 4) Dépendances logicielles

- Python 3 avec:
  - `Jetson.GPIO`
  - `jetson-inference` et `jetson-utils`
  - `pyserial`
- Outils système:
  - `espeak` (voix française)
  - `aplay` (ALSA)
- Droits/permissions: accès à `/dev/ttyTHS1` (chmod dans `startup_script.sh`).

## 5) Fonctionnement détaillé (flux d’exécution)

Séquence générale (`main.py`):

1. Initialisation: `Button(pin=11)`, `Vibration(pin=13)`, `UltrasonicSensor(/dev/ttyTHS1)`, `Camera(ssd-mobilenet-v2)`, `Sound(text_to_speech.sh)`.
2. Annonce de démarrage, annonce du mode courant (par défaut: « exploration »).
3. Boucle infinie:
   - Si appui détecté sur le bouton: bascule entre « exploration » ↔ « marche » et annonce le mode.
   - Si mode « exploration »:
     - Prend une image, détecte des objets.
     - Lit la distance ultrason.
     - Si objets détectés: annonce "<classe> à <distance en m>" pour chaque détection (distance calculée à partir de l’ultrason, pas de vision 3D).
     - Sinon: annonce « Aucun objet détecté ».
   - Si mode « marche »:
     - Lit la distance ultrason et annonce la valeur en mètres si elle est dans des plages définies (4–5 m, 3–4 m, etc.). Sinon dit « Rien ».

Notes d’implémentation:
- Anti-rebond bouton: simple `sleep(0.1)` dans `bouton.py`.
- Détection: `camera.get_detections()` retourne les objets; `Camera.get_class_name(id)` donne le libellé.
- Ultrason: lecture bloquante jusqu’à 4 octets, validation header 0xFF + checksum, conversion en cm. Retourne `None` si erreur ou < 30 cm (filtrage).
- TTS: chaque `speak()` lance un processus shell bloquant (`os.system`).

## 6) Contrats d’E/S (résumé)

- `Button.wait_for_press()` → `True` sur front montant propre (sinon `False`).
- `UltrasonicSensor.get_distance()` → `float` (cm) ou `None` si erreur/valeur < 30 cm.
- `Camera.get_detections()` → liste de détections (objets Jetson Inference) ou liste vide.
- `Sound.speak(text)` → produit de l’audio (synchrone, bloque pendant la parole).
- `Vibration.vibrate(seconds)` → active GPIO HIGH pendant `seconds`.

## 7) Points d’attention, risques et anomalies relevées

- Robustesse « distance None »:
  - Dans `main.py`, `format_distance_in_meters(distance)` est appelé immédiatement après la lecture, même si `distance` peut être `None`. Cela provoquera un `TypeError` (division par 100) en cas de lecture invalide. Idem en mode « marche » où le formatage est fait avant de vérifier la valeur.
  - Recommandation: ne formater la distance qu’après vérification `distance is not None`.
- Nettoyage caméra: `camera.cleanup()` n’est pas appelé dans le `finally` de `main.py` → fuite potentielle de ressource.
- Vibration non utilisée: `Vibration` est initialisée mais jamais déclenchée. C’est une fonctionnalité prévue mais absente de la logique.
- Bouton en polling: boucle d’interrogation avec `sleep(0.1)` → consomme CPU inutilement; préférer détection d’événements `GPIO.add_event_detect` avec `bouncetime`.
- TTS bloquant: `os.system` bloque la boucle principale pendant la synthèse, ce qui peut dégrader la réactivité.
- Bruit/Spam audio: en mode « exploration », annonce « Aucun objet détecté » très fréquemment → expérience utilisateur bruyante. Ajouter un tempo ou seuil de répétition.
- Scripts et chemins:
  - `startup_script.sh` pointe vers `/home/canneblancheintelligente/Documents/PRI_IRFAN/...` (avec underscore), différent du nom de dossier courant « PRI IRFAN » (avec espace) → risque d’incohérence selon l’arborescence de déploiement.
  - `text_to_speech.sh`: message d’erreur mentionne « easpeak » (typo) au lieu de `espeak`; l’index de carte son `SOUND_CARD_IDX=2` peut être à ajuster.
- Seuils ultrason: filtre < 30 cm peut masquer des obstacles proches; vérifier le besoin métier. Les seuils en mode « marche » sont en largeurs (200–500 cm) mais toute autre valeur déclenche « Rien ».
- Résilience: peu de gestion d’exceptions côté caméra/TTS; pas de watchdog ni de relance en cas d’échec récurrent.

## 8) Améliorations recommandées (courte liste actionnable)

1. Sécuriser l’usage de la distance:
   - Vérifier `distance is not None` avant tout calcul/formatage; ne pas prononcer si valeur invalide.
2. Nettoyage des ressources:
   - Appeler `camera.cleanup()` dans le `finally` de `main.py`.
3. Bouton événementiel:
   - Remplacer le polling par `GPIO.add_event_detect` pour une meilleure réactivité et moins de CPU.
4. TTS non-bloquant:
   - Passer à `subprocess.Popen` (ou file d’événements) pour ne pas bloquer la boucle; ajouter un rate-limit/anti-spam.
5. Utiliser le vibreur en « marche »:
   - Retour haptique quand la distance < X cm (pulses proportionnels).
6. Journalisation:
   - Remplacer `print` par `logging` avec niveaux et timestamps; option de log vers fichier.
7. Configuration externe:
   - Extraire paramètres (pins, seuils, modèle, carte son) dans un fichier `env.conf`/YAML.
8. Déploiement propre:
   - Fournir un service systemd (ExecStart, EnvironmentFile, After=sound.target) au lieu d’un script de lancement manuel.
9. Robustesse caméra/ultrason:
   - Timeouts/relances, vérification périodique de l’état, métriques.

## 9) Plan de tests (extraits)

- Unitaires rapides:
  - `format_distance_in_meters(None)` ne doit jamais être appelé; tester gardes autour.
  - Simulation de trames ultrason: cas OK (header 0xFF, checksum OK), checksum KO, < 30 cm, timeout.
- Intégration matérielle:
  - Détection d’objets (USB vs CSI), précision des libellés, charge CPU et latence TTS.
  - Bouton: rebonds, pressions rapides/lentes, bascule de mode fiable.
  - Vibration: cycle ON/OFF, intensité, alimentation.
- Endurance:
  - Exécution 1–2 h: pas de fuite, pas de crash, stabilité audio/vidéo/série.

## 10) Schéma de flux (texte)

- Démarrage → init modules → annoncer « exploration » → boucle:
  - [Bouton appuyé] → basculer mode → annoncer.
  - Si exploration → caméra.Detect + ultrason.get_distance → si détection: annonce <classe + distance m>, sinon (idéalement) silence ou annonce espacée.
  - Si marche → ultrason.get_distance → si distance dans plages: annonce distance m, sinon « Rien ».

## 11) Annexes utiles

- Brochage (mode BOARD): bouton=11 (IN, pull-down), vibration=13 (OUT).
- Caméra: `csi://0` (pour CSI). Pour USB: possiblement `/dev/video0`.
- Série: `/dev/ttyTHS1` (9600 bauds, timeout=1s).
- Script audio: `espeak -s 160 -v fr ... | aplay -D plughw:<index>,0`.

---

### Références fichiers (exemples)
- `main.py`: boucle modes, appels `format_distance_in_meters`, bascule bouton, TTS.
- `ultrasonic.py`: décodage trame, conversion en cm, filtrage < 30 cm.
- `camera.py`: `detectNet("ssd-mobilenet-v2")`, `videoSource("csi://0")`.
- `sound.py`: `os.system(text_to_speech.sh)`.
- `bouton.py`: anti-rebond 100 ms.
- `vibration.py`: non utilisé dans la logique actuelle.
- `startup_script.sh`: chmod UART + lancement main.

### Pistes de correction rapides (patchs à envisager)
- Déplacer la création de `formatted_distance` après les vérifications `distance is not None` dans les deux modes.
- Appeler `camera.cleanup()` dans `finally` de `main.py`.
- Corriger le message d’erreur `easpeak` → `espeak`.
- Ajouter un throttle pour « Aucun objet détecté ».
- Exploiter `vibration.vibrate()` en mode marche pour obstacles proches.
