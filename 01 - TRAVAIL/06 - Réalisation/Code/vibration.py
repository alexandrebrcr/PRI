# vibration.py
# Ce fichier gère le fonctionnement du vibreur connecté sur le pin 13

import Jetson.GPIO as GPIO
import time

class Vibration:

    def __init__(self, vibration_pin=13):
        """
        Initialisationd du vibreur
        :param vibration_pin: GPIO utilisé pour contrôler le vibreur (pin 13)
        """
        self.vibration_pin = vibration_pin  
        GPIO.setmode(GPIO.BOARD)  # Configuration des broches en mode BOARD (numérotation physique)
        GPIO.setup(self.vibration_pin, GPIO.OUT, initial=GPIO.LOW)  # Configure la broche en sortie, initialisée à LOW

    def vibrate(self, duration):
        """
        Active le vibreur pour une durée donnée avec sécurité d'arrêt.
        :param duration: Durée donnée en seconde
        """
        # print(f"Vibration activée pendant {duration} seconde(s).")
        try:
            GPIO.output(self.vibration_pin, GPIO.HIGH)  # Active le vibreur
            time.sleep(duration)  # Maintient le vibreur activé pendant la durée donnée
        finally:
            # Ce code s'exécute MÊME si le programme est tué pendant le sleep
            GPIO.output(self.vibration_pin, GPIO.LOW)  # Désactive le vibreur

    def cleanup(self):
        """
        Libère les ressources GPIO après utilisation.
        """
        # Force l'arrêt physique avant de libérer le GPIO
        try:
            GPIO.output(self.vibration_pin, GPIO.LOW)
        except Exception:
            pass
        GPIO.cleanup(self.vibration_pin)
        print("GPIO du vibreur nettoyé")

# Exemple d'utilisation
if __name__ == "__main__":
    """
    Test du vibreur pendant 0.5 seconde, puis attend 1 seconde.
    """
    try:
        # Initialisation du vibreur sur le GPIO 13
        vibreur = Vibration(vibration_pin=13)
        print("Test du vibreur")

        # Boucle de test pour activer et désactiver le vibreur
        while True:
            vibreur.vibrate(0.5)  # Active le vibreur pendant 0.5 seconde
            time.sleep(1)  # Attend 1 seconde avant de réactiver
    except KeyboardInterrupt:
        # Arrêt propre en cas d'interruption (Ctrl + C)
        print("Programme interrompu.")
    finally:
        # Nettoie les ressources GPIO
        vibreur.cleanup()
