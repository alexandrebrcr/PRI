# main.py
# Programme principal de la Canne Blanche
# Modes : MARCHE, EXPLORATION, MIXTE

# --- Imports ---
import time
import signal
import sys
from bouton import Button
from vibration import Vibration
from camera import Camera
from sound import Sound
from ultrasonic import UltrasonicSensor

# --- Helpers ---
def format_dist(d): 
    """Formate la distance pour le TTS (ex: 150)"""
    return f"{int(round(d))}"

def main():
    print("Initialisation du système...")

    # --- Initialisation des Composants ---
    # On groupe l'initialisation pour la clarté et la gestion d'erreur
    try:
        button = Button(button_pin=11)
        vibration_motor = Vibration(vibration_pin=13)
        ultrasonic_sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)
        sound = Sound(script_path="./text_to_speech.sh")
        
        # Caméra (peut être le point de blocage, gérer séparément si besoin)
        camera = Camera(model="ssd-inception-v2")
        
        # Délai post-boot pour l'audio
        time.sleep(2)
    except Exception as e:
        print(f"ERREUR FATALE INIT: {e}")
        return

    # --- Configuration ---
    MODES = ["MARCHE", "EXPLORATION", "MIXTE"]
    curr_mode_idx = 0
    
    sound.speak("Système démarré. Mode Marche.", priority=True)
    sound.speak("Trois modes disponibles. Pressez le bouton pour changer.", priority=True)
    print("Système démarré. Mode: MARCHE")

    # --- Gestion Arrêt (SIGTERM/SIGINT) ---
    running = True
    def stop_handler(sig, frame):
        nonlocal running
        running = False
        print("\nArrêt demandé...")
    
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    # --- Variables d'État ---
    last_vocal = 0.0
    last_vib = 0.0
    last_mode_chg = 0.0 
    vib_state = 0 # Pattern vibration (0=Long, 1=Court)

    # --- Fonction Locale : Vibration Radar ---
    def handle_vibration_logic(mode, dist, now):
        nonlocal last_vib, vib_state
        if mode == 0: # MARCHE
            if dist >= 200: return # Pas de vibration au-delà de 2m
        elif mode == 1: # MIXTE
            if dist >= 400: return # Pas de vibration au-delà de 4m

        # Zone Danger (< 50cm) -> Pattern alerte binaire
        if dist < 50:
            if vib_state == 0 and (now - last_vib > 0.2):
                vibration_motor.vibrate(0.35); last_vib = now; vib_state = 1
            elif vib_state == 1 and (now - last_vib > 0.45):
                vibration_motor.vibrate(0.10); last_vib = now; vib_state = 0
        
        # Zone Approche (50cm-2m) -> Fréquence proportionnelle
        else:
            vib_state = 0
            # Calcul intervalle (plus proche = plus fréquent)
            interval = 0.3 + ((dist - 50) / 150.0) * 1.2
            if now - last_vib > interval:
                vibration_motor.vibrate(0.1); last_vib = now

    # --- Boucle Principale ---
    try:
        while running:
            now = time.time()
            
            # 1. Gestion du Bouton (Prioritaire)
            if button.wait_for_press():
                if now - last_mode_chg > 2.0:
                    curr_mode_idx = (curr_mode_idx + 1) % len(MODES)
                    mode = MODES[curr_mode_idx]
                    
                    sound.speak(f"Mode {mode}", priority=True)
                    print(f"Mode -> {mode}")
                    last_mode_chg = now
                    time.sleep(0.5)
                continue

            # 2. Logique des Modes
            mode = MODES[curr_mode_idx]
            dist = ultrasonic_sensor.get_distance()

            if mode == "MARCHE":
                # --- Mode Marche ---
                if dist is not None and dist < 200:
                    if now - last_vocal > 1:
                        sound.speak(format_dist(dist))
                        last_vocal = now
                    handle_vibration_logic(0, dist, now)

            elif mode == "EXPLORATION":
                # --- Mode Exploration ---
                dets = camera.get_detections()
                if now - last_vocal > 2 and dets:
                    objs = []
                    for d in dets:
                        desc = f"{camera.get_class_name(d.ClassID)} {camera.get_object_position(d)}"
                        if desc not in objs: objs.append(desc)
                    
                    msg = ", ".join(objs)
                    print(f"[EXPLO] {msg}")
                    sound.speak(msg)
                    last_vocal = now

            elif mode == "MIXTE":
                # --- Mode Mixte ---
                if dist is not None and dist < 400:
                    dets = camera.get_detections()
                    
                    if now - last_vocal > 1:
                        # Filtrage : Uniquement objets 'devant'
                        objs = []
                        if dets:
                            for d in dets:
                                if camera.get_object_position(d) == "devant":
                                    name = camera.get_class_name(d.ClassID)
                                    if name not in objs: objs.append(name)
                        
                        # Construction message : "Chaise, Table 150" ou juste "150"
                        msg = f"{', '.join(objs)} {format_dist(dist)}" if objs else format_dist(dist)
                        print(f"[MIXTE] {msg}")
                        sound.speak(msg)
                        last_vocal = now
                    
                    handle_vibration_logic(1, dist, now)
                
                else:
                    # Flush buffer caméra si loin pour garder l'image à jour
                    camera.get_detections()

            # Petite pause CPU
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass # Arrêt Ctrl+C
    
    finally:
        # --- Nettoyage ---
        print("Fermeture du système...")
        sound.speak("Arrêt du système", priority=True)
        time.sleep(2.0)
        
        # Cleanup sécurisé
        for obj in [button, vibration_motor, ultrasonic_sensor, sound]:
            if obj: 
                try: obj.cleanup()
                except: pass
        
        if 'camera' in locals():
            try: camera.cleanup()
            except: pass

if __name__ == "__main__":
    main()