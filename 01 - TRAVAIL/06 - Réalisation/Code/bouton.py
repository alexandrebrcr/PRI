# bouton.py
# Ce fichier gère les appuis d'un bouton poussoir connecté au GPIO de la Jetson Nano sur le pin 11.
# Configuration : ACTIVE LOW (Câblage au GND)
# - Fil A -> GND
# - Fil B -> GPIO 11
# - Code -> Pull-Up interne activé

import Jetson.GPIO as GPIO
import time

class Button:

    def __init__(self, button_pin=11):
        """
        Initialise le bouton.
        """
        self.button_pin = button_pin
        # Variable pour savoir si on a déjà comptabilisé l'appui en cours
        self.is_held = False 

        # Configuration du GPIO
        GPIO.setmode(GPIO.BOARD)
        # On demande le Pull-Up, mais on sait que la Jetson peut l'ignorer
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def wait_for_press(self):
        """
        Détection simplifiée et robuste.
        Retourne True une seule fois quand le bouton passe à l'état BAS.
        """
        # On lit l'état actuel (LOW = Appuyé car connecté au GND)
        current_state = GPIO.input(self.button_pin)

        if current_state == GPIO.LOW:
            # Le bouton est physiquement appuyé
            if not self.is_held:
                # C'est un NOUVEL appui qu'on n'a pas encore traité
                self.is_held = True
                return True
            else:
                # On le sait déjà, l'utilisateur maintient le bouton
                return False
        else:
            # Le bouton est relâché (HIGH)
            self.is_held = False
            return False

    def cleanup(self):
        """
        Nettoie le GPIO.
        """
        GPIO.cleanup(self.button_pin)

# ==========================
# TEST UNITAIRE RAPIDE
# ==========================
if __name__ == "__main__":
    try:
        print("--- TEST BOUTON (Mode GND / Active Low) ---")
        print("Branchez le bouton entre PIN 11 et un GND.")
        button = Button(button_pin=11)
        
        while True:
            if button.wait_for_press():
                print(">> BOUTON APPUYÉ !")
                time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("Arrêt.")
    finally:
        if 'button' in locals():
            button.cleanup()