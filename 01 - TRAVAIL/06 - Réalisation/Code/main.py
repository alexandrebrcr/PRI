# main.py
# Programme principal de la Canne Blanche Intelligente
# Gère deux modes : 
# 1. Marche : Détection d'obstacles par ultrasons (< 2m)
# 2. Exploration : Reconnaissance d'objets par caméra

import time
import signal
import sys
from bouton import Button
from vibration import Vibration
from camera import Camera
from sound import Sound
from ultrasonic import UltrasonicSensor

def format_distance_message(distance_cm): 
    """
    Formate le message vocal pour la distance.
    :param distance_cm: Distance en centimètres.
    :return: Chaîne de caractères à prononcer (ex: "150")
    """
    #meters = distance_cm / 100
    return f"{distance_cm:.1f}"

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
    
    # Caméra AI - Changement pour Inception V2 (plus précis)
    camera = Camera(model="ssd-inception-v2")
    
    # Module Son
    sound = Sound(script_path="./text_to_speech.sh")

    # 2. Définition des modes
    # Mode 0 = Marche (Ultrasons)
    # Mode 1 = Exploration (Caméra)
    # Mode 2 = Mixte (Ultrasons + Caméra si obstacle)
    modes = ["MARCHE", "EXPLORATION", "MIXTE"]
    current_mode_index = 0
    
    sound.speak("Système démarré. Mode Marche.", priority=True)
    print("Système démarré. Mode Marche.")

    # Variable de contrôle de la boucle principale
    running = True

    # Gestion propre de l'arrêt via systemctl (SIGTERM)
    def signal_handler(signum, frame):
        # On passe simplement la variable à False pour finir la boucle proprement
        nonlocal running
        running = False
        print("\nSignal d'arrêt reçu. Fin de la boucle en cours...")
        
    signal.signal(signal.SIGTERM, signal_handler)
    # On capture aussi SIGINT (Ctrl+C) de la même façon pour être cohérent
    signal.signal(signal.SIGINT, signal_handler)

    # Variables de suivi temporel pour éviter le spam vocal
    last_vocal_announce_time = 0.0
    last_vibration_time = 0.0
    last_mode_change_time = 0.0 # Anti-rebond pour le changement de mode
    
    def gerer_vibration_radar(dist_cm, current_time):
        """Gestion progressive de la vibration façon radar de recul"""
        nonlocal last_vibration_time
        
        if dist_cm < 50:
            # DANGER IMMÉDIAT (< 50cm) : Vibration quasi-continue (intense)
            # On vibre 0.15s avec une pause minuscule
            if current_time - last_vibration_time > 0.2:
                vibration_motor.vibrate(0.15)
                last_vibration_time = current_time
                
        elif dist_cm < 200:
            # APPROCHE (50cm - 2m) : Fréquence proportionnelle
            # 50cm -> délai court (0.3s)
            # 200cm -> délai long (1.5s)
            ratio = (dist_cm - 50) / 150.0  # 0.0 à 1.0
            interval = 0.3 + (ratio * 1.2)
            
            if current_time - last_vibration_time > interval:
                vibration_motor.vibrate(0.1) # Vibration courte (blip)
                last_vibration_time = current_time

    try:
        while running:
            # ---------------------------------------------------------
            # 1. GESTION DU CHANGEMENT DE MODE (PRIORITAIRE)
            # ---------------------------------------------------------
            if button.wait_for_press():
                # On empêche de changer de mode trop vite (moins de 2s)
                if time.time() - last_mode_change_time < 2.0:
                    time.sleep(0.1)
                    continue

                # On passe au mode suivant
                current_mode_index = (current_mode_index + 1) % len(modes)
                current_mode = modes[current_mode_index]
                
                # Annonce du nouveau mode (PRIORITAIRE)
                sound.speak(f"Mode {current_mode}", priority=True)
                print(f" changement de mode -> {current_mode}")
                
                last_mode_change_time = time.time()
                
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
                        
                        # Gestion du délai entre les annonces vocales (toutes les 2)
                        if now - last_vocal_announce_time > 2:
                            msg = f"Obstacle {format_distance_message(distance)}"
                            print(f"[MARCHE] {msg}")
                            sound.speak(msg)
                            last_vocal_announce_time = now
                        
                        # Retour Haptique Proportionnel
                        gerer_vibration_radar(distance, now)

                    else:
                        pass
                
                time.sleep(0.1) # Petite pause pour ne pas surcharger le CPU

            elif current_mode == "EXPLORATION":
                # --- MODE EXPLORATION : Caméra Uniquement ---
                
                detections = camera.get_detections()
                
                # On ne parle que toutes les 2 secondes pour ne pas saturer
                if now - last_vocal_announce_time > 2:
                    if detections:
                        # On prend l'objet avec la plus grande confiance ou le premier
                        found_objects = []
                        for det in detections:
                            name = camera.get_class_name(det.ClassID)
                            pos = camera.get_object_position(det)
                            desc = f"{name} {pos}"
                            
                            if desc not in found_objects: 
                                found_objects.append(desc)
                        
                        if found_objects:
                            # Construit la phrase : "personne devant, chaise à droite"
                            phrase = ", ".join(found_objects)
                            print(f"[EXPLORATION] Vu : {phrase}")
                            sound.speak(phrase)
                            last_vocal_announce_time = now
                    else:
                        pass

            elif current_mode == "MIXTE":
                # --- MODE MIXTE : Ultrasons + Caméra si obstacle proche ---
                
                distance = ultrasonic_sensor.get_distance()
                
                if distance is not None and distance < 200:
                    # Obstacle à moins de 2m -> On regarde ce que c'est
                    
                    # On active la détection caméra
                    detections = camera.get_detections()
                    
                    found_objects = []
                    if detections:
                        for det in detections:
                            name = camera.get_class_name(det.ClassID)
                            pos = camera.get_object_position(det)
                            
                            # FILTRE MODE MIXTE : On ne garde que ce qui est DEVANT
                            if pos != "devant":
                                continue
                                
                            desc = f"{name}"
                            
                            if desc not in found_objects:
                                found_objects.append(desc)
                    
                    # Gestion vocale
                    if now - last_vocal_announce_time > 2:
                        if found_objects:
                            # C'est un objet connu
                            phrase = ", ".join(found_objects)
                            # On ajoute la distance à la phrase: "Chaise devant, 150"
                            full_msg = f"{phrase}, {format_distance_message(distance)}"
                            
                            print(f"[MIXTE] Vu : {full_msg}")
                            sound.speak(full_msg)
                        else:
                            # Pas d'objet connu -> "Obstacle 150"
                            msg = f"Obstacle {format_distance_message(distance)}"
                            print(f"[MIXTE] {msg}")
                            sound.speak(msg)
                        
                        last_vocal_announce_time = now
                    
                    # Vibration (Sécurité toujours active en mixte)
                    gerer_vibration_radar(distance, now)
                
                else:
                    # Si > 2m, on vide le buffer caméra pour éviter le lag (image fraîche)
                    # Cela garde le pipeline vidéo actif
                    camera.get_detections() 
                    pass

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Arrêt par l'utilisateur.")
    
    finally:
        # Nettoyage propre
        print("Nettoyage des ressources...")
        sound.speak("Arrêt du système", priority=True)
        # On laisse un peu de temps à la voix de finir
        time.sleep(2.0) 
        
        # On nettoie d'abord les périphériques robustes
        try:
            button.cleanup()
        except: pass
            
        try:
            vibration_motor.cleanup()
        except: pass
            
        try:
            ultrasonic_sensor.cleanup()
        except: pass
        
        try:
            sound.cleanup()
        except: pass

        # On garde la caméra pour la fin car elle risque de SegFault
        try:
            if 'camera' in locals():
                print("Arrêt de la caméra...")
                camera.cleanup()
        except Exception as e:
            print(f"Erreur fermeture caméra (ignorée): {e}")
        except:
            print("Crash critique fermeture caméra (ignoré)")

if __name__ == "__main__":
    main()
