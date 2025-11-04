# main.py
# Il combine les interactions entre les différents composants : bouton, caméra, vibreur, capteur ultrason et synthèse vocale.
# Le programme alterne entre deux modes : exploration et marche.

import time
from bouton import Button
from vibration import Vibration
from camera import Camera
from sound import Sound
from ultrasonic import UltrasonicSensor

def format_distance_in_meters(distance): 
    """
    Convertit une distance en centimètres en mètres avec une décimale.
    Exemple : 320 cm devient "3.2".
    :param distance: Distance en centimètres.
    :return: Distance en mètres
    """
    meters = distance / 100
    return f"{meters:.1f}"

def main():
    """
    Fonction principale qui gère l'exécution du projet.
    Elle initialise les composants, détecte les appuis sur le bouton pour changer de mode,
    et exécute les fonctionnalités propres à chaque mode.
    """
    # Initialisation des composants matériels
    button = Button(button_pin=11)  # Bouton connecté au GPIO 11
    vibration_motor = Vibration(vibration_pin=13)  # Vibreur connecté au GPIO 13
    ultrasonic_sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)  # Capteur ultrason
    camera = Camera()  # Caméra pour la détection d'objets
    sound = Sound(script_path="./text_to_speech.sh")  # Synthèse vocale avec espeak

    # Définition des modes disponibles
    modes = ["exploration", "marche"]  # Modes de fonctionnement
    current_mode_index = 0  # Index du mode actuel (par défaut : exploration)
    current_mode = modes[current_mode_index]

    # Annonce du démarrage du système
    sound.speak("Le système a démarré")

    # Annonce du mode initial
    sound.speak(f"Mode {current_mode}")
    print(f"Mode {current_mode}")

    # Variables d'état pour anti-spam/retours haptiques
    last_no_detection_announce_time = 0.0
    last_vibration_time = 0.0
    last_distance_error_announce_time = 0.0

    try:
        # Boucle principale pour gérer les fonctionnalités des deux modes
        while True:
            # Gestion du bouton pour changer de mode
            if button.wait_for_press():
                # Change le mode en alternant entre "exploration" et "marche"
                current_mode_index = (current_mode_index + 1) % len(modes)
                current_mode = modes[current_mode_index]
                sound.speak(f"Mode {current_mode}")
                print(f"Mode {current_mode}")
            
            # Mode exploration : détection avec la caméra et mesure de la distance
            if current_mode == "exploration":
                detections = camera.get_detections()  # Objets détectés par la caméra
                distance = ultrasonic_sensor.get_distance()  # Distance mesurée par le capteur ultrason
                if distance is not None:
                    print(f"{distance} centimètres")  # Affiche la distance brute

                if detections:
                    for detection in detections:
                        class_name = camera.get_class_name(detection.ClassID)
                        # Annonce si la distance est disponible
                        if distance is not None:
                            formatted_distance = format_distance_in_meters(distance)
                            sound.speak(f"{class_name} à {formatted_distance}")
                            print(f"{class_name} à {formatted_distance}")
                        else:
                            # Distance indisponible : annoncer seulement l'objet
                            sound.speak(f"{class_name}")
                            print(f"{class_name}")
                else:
                    # Aucune détection: annonce limitée à une fois toutes les 3 secondes
                    now = time.time()
                    if now - last_no_detection_announce_time > 3.0:
                        sound.speak("Aucun objet détecté")
                        print("Aucun objet détecté")
                        last_no_detection_announce_time = now

            # Mode marche : vérifie la distance et annonce de la distance
            elif current_mode == "marche":
                distance = ultrasonic_sensor.get_distance()
                if distance is not None:
                    formatted_distance = format_distance_in_meters(distance)
                    # Annonce si la distance se situe dans les plages définies
                    if 400 <= distance <= 500: # 4 à 5 mètres
                        sound.speak(f"{formatted_distance}")
                        print(f"{distance} centimètres")
                    elif 300 <= distance <= 400:
                        sound.speak(f"{formatted_distance}")
                        print(f"{distance} centimètres")
                    elif 200 <= distance <= 300:
                        sound.speak(f"{formatted_distance}")
                        print(f"{distance} centimètres")
                    elif distance < 200:
                        sound.speak(f"{formatted_distance}")
                        print(f"{distance} centimètres")
                        # Retour haptique pour obstacle proche, avec anti-spam (~0.5s)
                        now = time.time()
                        if now - last_vibration_time > 0.5:
                            vibration_motor.vibrate(0.1)
                            last_vibration_time = now
                    else:
                        sound.speak("Rien")
                        time.sleep(0.25)
                else:
                    # Erreur lors de la lecture de la distance (anti-spam)
                    now = time.time()
                    if now - last_distance_error_announce_time > 3.0:
                        sound.speak("Erreur de lecture de distance")
                        print("Erreur de lecture de distance")
                        last_distance_error_announce_time = now

    except KeyboardInterrupt:
        # Interrompt proprement le programme avec Ctrl + C
        print("Programme arrêté par l'utilisateur.")
    finally:
        # Nettoie les ressources matérielles
        button.cleanup()
        vibration_motor.cleanup()
        ultrasonic_sensor.cleanup()
        try:
            camera.cleanup()
        except Exception:
            pass
        try:
            sound.cleanup()
        except Exception:
            pass
        print("Nettoyage complet")

if __name__ == "__main__":
    # Point d'entrée principal
    main()
