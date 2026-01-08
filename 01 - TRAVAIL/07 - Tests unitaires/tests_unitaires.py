import unittest
import sys
import time
from unittest.mock import MagicMock, patch

# --- MOCKING DES BIBLIOTHEQUES MATERIELLES ---
# Ces lignes sont indispensables pour tester le code sans être sur la Jetson Nano
# On crée de fausses bibliothèques qui simulent les vraies.

# 1. Mock Jetson.GPIO
mock_gpio = MagicMock()
mock_gpio.BOARD = 'BOARD'
mock_gpio.IN = 'IN'
mock_gpio.OUT = 'OUT'
mock_gpio.HIGH = 1
mock_gpio.LOW = 0
mock_gpio.PUD_DOWN = 'PUD_DOWN'
mock_gpio.RISING = 'RISING'
sys.modules['Jetson.GPIO'] = mock_gpio
sys.modules['Jetson'] = MagicMock()

# 2. Mock Jetson Inference / Utils
mock_inference = MagicMock()
sys.modules['jetson_inference'] = mock_inference
mock_utils = MagicMock()
sys.modules['jetson_utils'] = mock_utils

# 3. Mock Serial (pour Ultrason)
sys.modules['serial'] = MagicMock()


# --- IMPORT DES MODULES A TESTER ---
# On importe les fichiers de votre projet après avoir mocké les dépendances
from bouton import Button
from vibration import Vibration
from ultrasonic import UltrasonicSensor
from sound import Sound
from camera import Camera
from main import format_distance_message

class TestProjetCanne(unittest.TestCase):

    # =================================================================
    # TESTS DU MODULE BOUTON (bouton.py)
    # =================================================================
    def test_bouton_initialisation(self):
        """Test BTN-01: Vérifie l'initialisation correcte du GPIO"""
        btn = Button(button_pin=11)
        mock_gpio.setmode.assert_called_with(mock_gpio.BOARD)
        mock_gpio.setup.assert_called_with(11, mock_gpio.IN, pull_up_down=mock_gpio.PUD_DOWN)

    def test_bouton_detection_evenement(self):
        """Test BTN-02: Vérifie que le flag s'active sur interruption"""
        btn = Button(11)
        # On simule le déclenchement du callback _on_press
        btn._on_press(11)
        
        # Le flag interne doit être True, donc wait_for_press doit renvoyer True
        self.assertTrue(btn.wait_for_press())
        # Après consommation, il doit repasser à False
        self.assertFalse(btn.wait_for_press())

    def test_bouton_fallback_polling(self):
        """Test BTN-03: Vérifie le mode manuel (polling) si les événements échouent"""
        btn = Button(11)
        # On force le flag à False
        btn._pressed_flag = False
        
        # Scénario : last_state est LOW, et on lit HIGH (appui)
        btn.last_state = mock_gpio.LOW
        mock_gpio.input.side_effect = [mock_gpio.HIGH, mock_gpio.HIGH] # Deux lectures HIGH (une immédiate, une après debounce)
        
        # On doit détecter l'appui
        self.assertTrue(btn.wait_for_press())

    # =================================================================
    # TESTS DU MODULE VIBRATION (vibration.py)
    # =================================================================
    def test_vibration_activation(self):
        """Test VIB-02: Vérifie la séquence ON/OFF du vibreur"""
        vib = Vibration(13)
        duree = 0.1
        
        with patch('time.sleep') as mock_sleep:
            vib.vibrate(duree)
            
            # Vérifie qu'on a mis le pin à HIGH (ON)
            mock_gpio.output.assert_any_call(13, mock_gpio.HIGH)
            # Vérifie qu'on a attendu la bonne durée
            mock_sleep.assert_called_with(duree)
            # Vérifie qu'on a remis le pin à LOW (OFF)
            mock_gpio.output.assert_called_with(13, mock_gpio.LOW)

    # =================================================================
    # TESTS DU MODULE ULTRASON (ultrasonic.py)
    # =================================================================
    @patch('serial.Serial')
    def test_ultrason_distance_valide(self, mock_serial_cls):
        """Test US-02: Vérifie le calcul de distance avec des données valides"""
        # Configuration du mock série
        mock_conn = MagicMock()
        mock_serial_cls.return_value = mock_conn
        mock_conn.is_open = True
        
        # Simulation d'une trame valide : 
        # Header=0xFF, High=0x05, Low=0xDC (1500mm), Checksum=(0xFF+0x05+0xDC)&0xFF
        # 0xFF + 0x05 + 0xDC = 255 + 5 + 220 = 480. 480 & 0xFF = 224 (0xE0)
        data = b'\xFF\x05\xDC\xE0' 
        mock_conn.read.return_value = data
        
        sensor = UltrasonicSensor()
        dist = sensor.get_distance()
        
        # 1500 mm = 150.0 cm
        self.assertEqual(dist, 150.0)

    @patch('serial.Serial')
    def test_ultrason_checksum_invalide(self, mock_serial_cls):
        """Test US-03: Vérifie le rejet des données corrompues"""
        mock_conn = MagicMock()
        mock_serial_cls.return_value = mock_conn
        mock_conn.read.return_value = b'\xFF\x00\x00\x00' # Checksum faux
        
        sensor = UltrasonicSensor()
        dist = sensor.get_distance()
        self.assertIsNone(dist)

    # =================================================================
    # TESTS DU MODULE SON (sound.py)
    # =================================================================
    @patch('subprocess.run')
    def test_son_parole(self, mock_subprocess):
        """Test SND-02: Vérifie l'appel au script bash"""
        sound = Sound(script_path="./fake_script.sh")
        
        # On envoie un message
        sound.speak("Test")
        
        # On attend un peu que le thread worker le traite
        time.sleep(0.1)
        
        # Vérifie que subprocess.run a été appelé avec les bons arguments
        mock_subprocess.assert_called_with(["./fake_script.sh", "Test"], check=False)
        sound.cleanup()

    # =================================================================
    # TESTS DU MODULE CAMERA (camera.py)
    # =================================================================
    def test_camera_detection(self):
        """Test CAM-02: Vérifie la récupération des détections"""
        cam = Camera()
        
        # Mock de l'image capturée
        mock_img = MagicMock()
        cam.camera.Capture.return_value = mock_img
        
        # Mock des détections retournées par le réseau
        mock_detect = MagicMock()
        mock_detect.ClassID = 1
        mock_detect.Confidence = 0.95
        cam.net.Detect.return_value = [mock_detect]
        
        detections = cam.get_detections()
        
        # Vérifications
        cam.camera.Capture.assert_called()
        cam.net.Detect.assert_called_with(mock_img)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].Confidence, 0.95)

    def test_camera_image_vide(self):
        """Test CAM-03: Vérifie le comportement si la caméra ne renvoie rien"""
        cam = Camera()
        cam.camera.Capture.return_value = None
        
        detections = cam.get_detections()
        self.assertEqual(detections, [])

    # =================================================================
    # TESTS UTILITAIRES MAIN (main.py)
    # =================================================================
    def test_format_message(self):
        """Test MAIN-01: Vérifie le formatage du message de distance"""
        msg = format_distance_message(150.56)
        self.assertEqual(msg, "150.6") # Arrondi à 1 décimale

if __name__ == '__main__':
    unittest.main()