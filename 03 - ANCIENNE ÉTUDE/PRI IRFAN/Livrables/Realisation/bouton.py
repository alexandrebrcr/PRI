# bouton.py
# Ce fichier permet de gérer les appuie d'un bouton poussoir connecter au GPIO de la Jetson Nano sur le pin 11.
# Le bouton est configuré pour détecter les appuis avec un mode pull-down.

import Jetson.GPIO as GPIO
import time

class Button:

    def __init__(self, button_pin=11):
        """
        Initialise le bouton.
        :param button_pin: Numéro du GPIO auquel le bouton est connecté (mode BOARD).
        """
        self.button_pin = button_pin
        self.last_state = GPIO.LOW  # État précédent du bouton.
        self.debounce_time = 0.1  # Temps de rebond pour éviter les détections multiples.

        # Configuration du GPIO en mode BOARD (numérotation physique des broches).
        GPIO.setmode(GPIO.BOARD)

        # Configuration du pin du bouton en entrée avec pull-down.
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def wait_for_press(self):
        """
        Vérifie si le bouton a été pressé en évitant les rebonds.
        :return: True si un appui est détecté, sinon False.
        """
        current_state = GPIO.input(self.button_pin)  # Lire l'état actuel du bouton.
        
        # Détection de la transition de LOW à HIGH (bouton pressé).
        if current_state == GPIO.HIGH and self.last_state == GPIO.LOW:
            # Pause pour éviter les rebonds.
            time.sleep(self.debounce_time)
            # Vérifie à nouveau si le bouton est toujours pressé.
            if GPIO.input(self.button_pin) == GPIO.HIGH:
                self.last_state = GPIO.HIGH
                return True
        elif current_state == GPIO.LOW:
            # Met à jour l'état précédent lorsque le bouton est relâché.
            self.last_state = GPIO.LOW

        return False

    def cleanup(self):
        """
        Nettoie le GPIO du pin pour éviter les conflits après l'exécution du programme.
        """
        GPIO.cleanup(self.button_pin)

# Exemple d'utilisation
if __name__ == "__main__":
    """
    Test du bouton en tant que script principal.
    Appuyez sur le bouton pour afficher un message dans le terminal.
    """
    try:
        button = Button(button_pin=11)  # Initialisation avec le GPIO 11.
        print("Appuyez sur le bouton pour tester...")
        while True:
            # Si le bouton est pressé, affiche un message.
            if button.wait_for_press():
                print("Bouton appuyé !")
                time.sleep(0.5)  # Pause pour éviter les détections rapides.
    except KeyboardInterrupt:
        # Arrêt propre du programme lors d'un Ctrl + C.
        print("Programme arrêté par l'utilisateur.")
    finally:
        # Nettoie les ressources utilisées.
        button.cleanup()
