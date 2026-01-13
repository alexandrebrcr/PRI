import unittest
import sys
import time
import os

import Jetson.GPIO as GPIO
from bouton import Button
from vibration import Vibration
from ultrasonic import UltrasonicSensor
from sound import Sound
from camera import Camera
from main import format_distance_message

class TestMaterielReel(unittest.TestCase):

    def setUp(self):
        """Nettoyage GPIO avant chaque test pour éviter les conflits"""
        try:
            GPIO.cleanup()
        except:
            pass
        time.sleep(1)

    def test_01_bouton_physique(self):
        """
        Test BTN-01 (Physique) : Test du bouton.
        ACTION REQUISE : Appuyez sur le bouton quand on vous le demande.
        """
        print("\n\n--- TEST DU BOUTON ---")
        print("Initialisation du bouton sur le pin 11...")
        btn = Button(button_pin=11)
        
        print(">>> VEUILLEZ APPUYER SUR LE BOUTON MAINTENANT (Vous avez 5 secondes) <<<")
        start_time = time.time()
        pressed = False
        
        while time.time() - start_time < 5.0:
            if btn.wait_for_press():
                pressed = True
                break
            time.sleep(0.1)
            
        self.assertTrue(pressed, "ECHEC : Aucun appui détecté en 5 secondes !")
        print("SUCCÈS : Appui détecté !")
        btn.cleanup()

    def test_02_vibration_physique(self):
        """
        Test VIB-01 (Physique) : Test du vibreur.
        ACTION REQUISE : Vérifiez si ça vibre.
        """
        print("\n\n--- TEST DU VIBREUR ---")
        vib = Vibration(vibration_pin=13)
        
        print(">>> ATTENTION : Le moteur va vibrer 3 fois <<<")
        for i in range(3):
            print(f"Vibration {i+1}/3...")
            vib.vibrate(0.3)
            time.sleep(0.5)
            
        # Pas d'assertion logicielle possible sur le ressenti, on assume que si pas d'erreur, c'est OK électriquement
        print("SUCCÈS : Commande envoyée sans erreur électrique.")
        vib.cleanup()

    def test_03_son_physique(self):
        """
        Test SND-01 (Physique) : Test audio.
        ACTION REQUISE : Vérifiez si vous entendez la voix.
        """
        print("\n\n--- TEST AUDIO ---")
        sound = Sound()
        
        phrase = "Test audio, un, deux, un, deux."
        print(f"Le système va dire : '{phrase}'")
        sound.speak(phrase, priority=True)
        
        # On attend un peu que ce soit dit
        time.sleep(4)
        print("SUCCÈS : Commande audio envoyée.")
        sound.cleanup()

    def test_04_ultrason_physique(self):
        """
        Test US-01 (Physique) : Lecture du capteur série.
        """
        print("\n\n--- TEST ULTRASON ---")
        try:
            us = UltrasonicSensor(port="/dev/ttyTHS1")
        except Exception as e:
            self.fail(f"Impossible d'ouvrir le port série : {e}")

        print("Lecture de 5 valeurs... Bougez la main devant le capteur.")
        valeurs_valides = 0
        for i in range(5):
            dist = us.get_distance()
            if dist is not None:
                print(f"Mesure {i+1}: {dist} cm")
                valeurs_valides += 1
            else:
                print(f"Mesure {i+1}: Erreur lecture")
            time.sleep(0.5)
        
        # On veut au moins 1 mesure valide sur 5 pour considérer que le capteur marche
        self.assertGreater(valeurs_valides, 0, "ECHEC : Aucune donnée valide reçue du capteur ultrason.")
        print("SUCCÈS : Données reçues.")
        us.cleanup()

    def test_05_camera_physique(self):
        """
        Test CAM-01 (Physique) : Capture d'une image et inférence.
        """
        print("\n\n--- TEST CAMERA ---")
        print("Chargement du modèle Inception V2 (peut être long)...")
        cam = Camera(model="ssd-inception-v2")
        
        print("Capture d'une image test...")
        # On essaie de récupérer une détection, même vide, ça prouve que le pipeline marche
        try:
            dets = cam.get_detections()
            print(f"Objets détectés instantanément : {len(dets)}")
            if len(dets) > 0:
                for d in dets:
                    print(f" - {cam.get_class_name(d.ClassID)} ({d.Confidence:.2f})")
        except Exception as e:
            self.fail(f"Erreur lors de la capture/inférence : {e}")
            
        print("SUCCÈS : Pipeline caméra fonctionnel.")
        cam.cleanup()

if __name__ == '__main__':
    # On force l'affichage verbeux pour voir les directives
    unittest.main(verbosity=2)
