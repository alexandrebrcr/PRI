import unittest
import time
import sys
import Jetson.GPIO as GPIO

from bouton import Button
from vibration import Vibration
from ultrasonic import UltrasonicSensor
from sound import Sound
from camera import Camera
from main import format_distance_message

class TestIntegrationReel(unittest.TestCase):
    """
    Tests d'intégration sur matériel réel (Jetson Nano).
    Ces tests vérifient que les composants fonctionnent ENSEMBLE.
    """

    @classmethod
    def setUpClass(cls):
        """Initialisation globale (une seule fois pour la caméra car c'est long)"""
        print("\n=== PRÉPARATION DES TESTS D'INTÉGRATION ===")
        print("Chargement de tous les drivers... (Patience ~1-2 min)")
        
        try:
            cls.sound = Sound()
            cls.sound.speak("Mode Test Intégration", priority=True)
            
            cls.btn = Button(button_pin=11)
            cls.vib = Vibration(vibration_pin=13)
            cls.us = UltrasonicSensor(port="/dev/ttyTHS1")
            cls.camera = Camera(model="ssd-inception-v2")
            
            print("Tous les composants sont prêts.")
            time.sleep(2)
        except Exception as e:
            print(f"FATAL: Echec init composants: {e}")
            sys.exit(1)

    @classmethod
    def tearDownClass(cls):
        """Nettoyage global à la fin"""
        print("\n=== FIN DES TESTS ===")
        cls.sound.speak("Fin des tests", priority=True)
        time.sleep(1)
        
        cls.btn.cleanup()
        cls.vib.cleanup()
        cls.us.cleanup()
        cls.camera.cleanup()
        cls.sound.cleanup()
        GPIO.cleanup()

    def test_INT_01_Scenario_Marche(self):
        """
        SCENARIO 1 : Mode MARCHE (Ultrasons -> Son + Vibration)
        Simule 10 secondes de fonctionnement.
        """
        print("\n--- SCENARIO 1 : MODE MARCHE (10s) ---")
        print("ACTION : Mettez votre main devant le capteur pour tester la réaction.")
        self.sound.speak("Test Mode Marche. Avancez la main.", priority=True)
        
        start_time = time.time()
        last_feedback = 0
        
        while time.time() - start_time < 10:
            # 1. Lecture Capteur
            dist = self.us.get_distance()
            
            # 2. Logique Intégration
            if dist is not None and dist < 200:
                print(f"Distance perçue : {dist} cm")
                
                now = time.time()
                if now - last_feedback > 1.5:
                    # Feedback Sonore
                    msg = f"Obstacle {format_distance_message(dist)}"
                    self.sound.speak(msg)
                    
                    # Feedback Haptique
                    self.vib.vibrate(0.1)
                    
                    last_feedback = now
            
            time.sleep(0.1)

    def test_INT_02_Scenario_Exploration(self):
        """
        SCENARIO 2 : Mode EXPLORATION (Caméra -> Son)
        Simule 10 secondes de fonctionnement.
        """
        print("\n--- SCENARIO 2 : MODE EXPLORATION (10s) ---")
        print("ACTION : Montrez des objets (Chaise, Bouteille, Personne) à la caméra.")
        self.sound.speak("Test Mode Exploration. Montrez des objets.", priority=True)
        
        start_time = time.time()
        last_speak = 0
        
        while time.time() - start_time < 10:
            # 1. Lecture Caméra
            detections = self.camera.get_detections()
            
            # 2. Logique Intégration
            if detections:
                now = time.time()
                if now - last_speak > 2.0:
                    found = []
                    for det in detections:
                        name = self.camera.get_class_name(det.ClassID)
                        pos = self.camera.get_object_position(det)
                        desc = f"{name} {pos}"
                        if desc not in found:
                            found.append(desc)
                    
                    if found:
                        phrase = ", ".join(found)
                        print(f"Vu : {phrase}")
                        self.sound.speak(phrase)
                        last_speak = now
                
    def test_INT_03_Interaction_Utilisateur(self):
        """
        SCENARIO 3 : Changement de mode
        Vérifie que le bouton interrompt ou trigger une action.
        """
        print("\n--- SCENARIO 3 : BOUTON & MODES ---")
        print("ACTION : Appuyez sur le bouton pour valider ce test.")
        self.sound.speak("Appuyez sur le bouton s'il vous plaît.", priority=True)
        
        pressed = False
        timeout = time.time() + 10
        
        while time.time() < timeout:
            if self.btn.wait_for_press():
                print("Bouton détecté !")
                self.sound.speak("Bouton reçu. Bravo.", priority=True)
                pressed = True
                break
            time.sleep(0.1)
            
        self.assertTrue(pressed, "Le bouton n'a pas été appuyé à temps.")

if __name__ == '__main__':
    unittest.main(verbosity=2)
