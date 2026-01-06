# main.py
# Programme principal de la Canne Blanche Intelligente
# Gère deux modes : 
# 1. Marche : Détection d'obstacles par ultrasons (< 2m)
# 2. Exploration : Reconnaissance d'objets par caméra

import time
from bouton import Button
from vibration import Vibration
from camera import Camera
from sound import Sound
from ultrasonic import UltrasonicSensor

def format_distance_message(distance_cm): 
    """
    Formate le message vocal pour la distance.
    :param distance_cm: Distance en centimètres.
    :return: Chaîne de caractères à prononcer (ex: "1.5 mètres")
    """
    meters = distance_cm / 100
    return f"{meters:.1f} mètres"

def main():
    """
    Boucle principale du programme.
    """
    print("Initialisation du système...")
    
    # 1. Initialisation des composants
    # Bouton sur GPIO 11
    try:
        button = Button(button_pin=11)
    except Exception as e:
        print(f"Erreur init bouton: {e}")
        return

    # Vibreur sur GPIO 13
    try:
        vibration_motor = Vibration(vibration_pin=13)
    except Exception as e:
        print(f"Erreur init vibreur: {e}")
        return

    # Capteur Ultrason sur le port série
    ultrasonic_sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)
    
    # Caméra AI
    camera = Camera()
    
    # Module Son
    sound = Sound(script_path="./text_to_speech.sh")

    # 2. Définition des modes
    # Mode 0 = Marche (Ultrasons)
    # Mode 1 = Exploration (Caméra)
    modes = ["MARCHE", "EXPLORATION"]
    current_mode_index = 0
    
    sound.speak("Système démarré. Mode Marche.")
    print("Système démarré. Mode Marche.")

    # Variables de suivi temporel pour éviter le spam vocal
    last_vocal_announce_time = 0.0
    last_vibration_time = 0.0
    
    try:
        while True:
            # ---------------------------------------------------------
            # 1. GESTION DU CHANGEMENT DE MODE (PRIORITAIRE)
            # ---------------------------------------------------------
            if button.wait_for_press():
                # On passe au mode suivant
                current_mode_index = (current_mode_index + 1) % len(modes)
                current_mode = modes[current_mode_index]
                
                # Annonce du nouveau mode
                sound.speak(f"Mode {current_mode}")
                print(f" changement de mode -> {current_mode}")
                
                # Petite pause pour éviter de changer 2 fois si appui très long
                time.sleep(0.5)
                continue # On redémarre la boucle proprement dans le nouveau mode

            # ---------------------------------------------------------
            # 2. COMPORTEMENT SELON LE MODE
            # ---------------------------------------------------------
            now = time.time()
            current_mode = modes[current_mode_index]

            if current_mode == "MARCHE":
                # --- MODE MARCHE : Ultrasons Uniquement (< 2m) ---
                
                distance = ultrasonic_sensor.get_distance()
                
                if distance is not None:
                    # Logique demandée : "Obstacle 2m" si < 2m.
                    if distance < 200: # Distance inférieure à 2 mètres
                        
                        # Gestion du délai entre les annonces vocales (toutes les 2.5s)
                        if now - last_vocal_announce_time > 2.5:
                            msg = f"Obstacle {format_distance_message(distance)}"
                            print(f"[MARCHE] {msg}")
                            sound.speak(msg)
                            last_vocal_announce_time = now
                        
                        # Retour Haptique (Vibration) plus fréquent si obstacle proche
                        # Vibration courte toutes les 1s max
                        if now - last_vibration_time > 1.0:
                            vibration_motor.vibrate(0.15)
                            last_vibration_time = now
                    else:
                        # Si distance >= 2m, on ne dit rien (mode exploration "sûr")
                        # Optionnel : décommenter pour debug
                        # print(f"[MARCHE] Voie libre ({distance} cm)")
                        pass
                
                time.sleep(0.1) # Petite pause pour ne pas surcharger le CPU

            elif current_mode == "EXPLORATION":
                # --- MODE EXPLORATION : Caméra Uniquement ---
                
                detections = camera.get_detections()
                
                # On ne parle que toutes les 3/4 secondes pour ne pas saturer
                if now - last_vocal_announce_time > 3.0:
                    if detections:
                        # On prend l'objet avec la plus grande confiance ou le premier
                        # Ici on liste tout ce qu'on voit
                        found_objects = []
                        for det in detections:
                            name = camera.get_class_name(det.ClassID)
                            if name not in found_objects: # Évite de dire "personne, personne"
                                found_objects.append(name)
                        
                        if found_objects:
                            # Construit la phrase : "Personne, Chaise"
                            phrase = ", ".join(found_objects)
                            print(f"[EXPLORATION] Vu : {phrase}")
                            sound.speak(phrase)
                            last_vocal_announce_time = now
                    else:
                        # Optionnel : dire "Rien" ?
                        # sound.speak("Rien") 
                        pass

    except KeyboardInterrupt:
        print("Arrêt par l'utilisateur.")
        sound.speak("Arrêt du système")
    
    finally:
        # Nettoyage propre
        print("Nettoyage des ressources...")
        button.cleanup()
        vibration_motor.cleanup()
        ultrasonic_sensor.cleanup()
        try:
            camera.cleanup()
        except:
            pass
        try:
            sound.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
