import unittest
import sys
import time
from unittest.mock import MagicMock, patch

# --- 1. MOCKING GLOBAL (Indispensable hors Jetson) ---
# On doit mocker les modules matériels AVANT d'importer main.py
sys.modules['Jetson.GPIO'] = MagicMock()
sys.modules['Jetson'] = MagicMock()
sys.modules['jetson_inference'] = MagicMock()
sys.modules['jetson_utils'] = MagicMock()
sys.modules['serial'] = MagicMock()

# Import du programme principal
import main

class TestIntegrationCanne(unittest.TestCase):

    def setUp(self):
        """Préparation avant chaque test"""
        # On patch les classes utilisées dans main.py pour contrôler leur comportement
        self.patcher_btn = patch('main.Button')
        self.patcher_vib = patch('main.Vibration')
        self.patcher_us = patch('main.UltrasonicSensor')
        self.patcher_cam = patch('main.Camera')
        self.patcher_snd = patch('main.Sound')
        
        # Démarrage des patchs
        self.MockButton = self.patcher_btn.start()
        self.MockVibration = self.patcher_vib.start()
        self.MockUltrasonic = self.patcher_us.start()
        self.MockCamera = self.patcher_cam.start()
        self.MockSound = self.patcher_snd.start()
        
        # On récupère les instances simulées pour vérifier les appels
        self.btn_instance = self.MockButton.return_value
        self.vib_instance = self.MockVibration.return_value
        self.us_instance = self.MockUltrasonic.return_value
        self.cam_instance = self.MockCamera.return_value
        self.snd_instance = self.MockSound.return_value

    def tearDown(self):
        """Nettoyage après chaque test"""
        patch.stopall()

    def run_main_one_loop(self):
        """
        Astuce : Exécute main() mais force une sortie après une itération
        en levant une exception via time.sleep ou une autre méthode contrôlée.
        """
        # On utilise side_effect sur time.sleep pour arrêter la boucle infinie proprement
        # La première fois ça passe, la seconde ça lève une erreur pour stop le test
        with patch('main.time.sleep', side_effect=[None, None, KeyboardInterrupt]):
            try:
                main.main()
            except KeyboardInterrupt:
                pass

    # =================================================================
    # SCÉNARIOS DE TEST
    # =================================================================

    def test_INT_01_demarrage_systeme(self):
        """Test INT-01: Vérifie l'initialisation et le message de bienvenue"""
        # Configuration : Bouton ne fait rien
        self.btn_instance.wait_for_press.return_value = False
        
        self.run_main_one_loop()
        
        # Vérifications
        # 1. Tous les composants doivent être initialisés
        self.MockButton.assert_called_with(button_pin=11)
        self.MockVibration.assert_called_with(vibration_pin=13)
        self.MockUltrasonic.assert_called()
        self.MockCamera.assert_called()
        
        # 2. Le message de démarrage doit être prononcé
        self.snd_instance.speak.assert_any_call("Système démarré. Mode Marche.")

    def test_INT_02_changement_mode(self):
        """Test INT-02: Vérifie le basculement Marche -> Exploration via Bouton"""
        # Configuration : 
        # 1er appel wait_for_press -> True (Appui détecté, changement mode)
        # 2ème appel wait_for_press -> False (Pas d'appui, exécution du mode)
        self.btn_instance.wait_for_press.side_effect = [True, False, False]
        
        self.run_main_one_loop()
        
        # Vérifications
        # On s'attend à ce que le système dise "Mode EXPLORATION"
        self.snd_instance.speak.assert_any_call("Mode EXPLORATION")

    def test_INT_03_detection_obstacle_marche(self):
        """Test INT-03: Vérifie alerte Son + Vibreur en Mode Marche"""
        # Configuration :
        self.btn_instance.wait_for_press.return_value = False # Pas de changement mode
        self.us_instance.get_distance.return_value = 150.0    # Obstacle à 150cm
        
        self.run_main_one_loop()
        
        # Vérifications
        # 1. Message vocal "Obstacle 150.0"
        self.snd_instance.speak.assert_called_with("Obstacle 150.0")
        # 2. Vibration activée
        self.vib_instance.vibrate.assert_called()

    def test_INT_05_reconnaissance_objet_exploration(self):
        """Test INT-05: Vérifie la détection caméra en Mode Exploration"""
        # Configuration complexe :
        # Il faut d'abord passer en mode Exploration (1 appui bouton)
        # Puis simuler une détection caméra
        
        # Séquence bouton : [Changement Mode (True), Pas d'appui (False)]
        self.btn_instance.wait_for_press.side_effect = [True, False]
        
        # Simulation détection caméra
        mock_detection = MagicMock()
        mock_detection.ClassID = 1
        # Simulation de la méthode get_class_name pour renvoyer "Chaise"
        self.cam_instance.get_detections.return_value = [mock_detection]
        self.cam_instance.get_class_name.return_value = "Chaise"
        
        self.run_main_one_loop()
        
        # Vérifications
        # 1. Vérifie qu'on est bien passé en exploration
        self.snd_instance.speak.assert_any_call("Mode EXPLORATION")
        # 2. Vérifie qu'on a annoncé l'objet
        self.snd_instance.speak.assert_called_with("Chaise")

if __name__ == '__main__':
    unittest.main()