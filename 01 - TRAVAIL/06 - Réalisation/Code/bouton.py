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
    self.last_state = GPIO.LOW  # État précédent du bouton (mis à jour après setup).
        self.debounce_time = 0.1  # Temps de rebond pour éviter les détections multiples.
        self._pressed_flag = False  # Indique qu'un front montant a été détecté.
    self._armed = False  # Devient True après avoir vu un état bas (évite faux positif au démarrage).

        # Configuration du GPIO en mode BOARD (numérotation physique des broches).
        GPIO.setmode(GPIO.BOARD)

    # Configuration de la broche en entrée.
    # NOTE: Sur Jetson, pull_up_down est ignoré. Prévoir une résistance externe.
    GPIO.setup(self.button_pin, GPIO.IN)

    # Laisse le signal se stabiliser puis initialise l'état.
    time.sleep(0.02)
    self.last_state = GPIO.input(self.button_pin)
    # On n'arme la détection qu'après avoir observé un état bas (bouton relâché).
    self._armed = (self.last_state == GPIO.LOW)

        # Détection d'événement sur front montant pour éviter le polling constant.
        try:
            GPIO.add_event_detect(
                self.button_pin,
                GPIO.RISING,
                callback=self._on_press,
                bouncetime=int(self.debounce_time * 1000)
            )
        except Exception:
            # Si l'événement n'est pas disponible, on tombera sur le fallback dans wait_for_press()
            pass

    def _on_press(self, channel):
        """
        Callback déclenché lors d'un front montant (appui bouton).
        """
        # N'accepte l'appui que si un état bas a été observé auparavant.
        if self._armed:
            self._pressed_flag = True

    def wait_for_press(self):
        """
        Vérifie si le bouton a été pressé en évitant les rebonds.
        :return: True si un appui est détecté, sinon False.
        """
        # Si un événement a été détecté, consommer le flag et retourner True
        if self._pressed_flag:
            self._pressed_flag = False
            # Désarme jusqu'à ce que le bouton soit relâché (état bas observé)
            self._armed = False
            return True

        # Fallback par polling si add_event_detect n'a pas pu être configuré
        current_state = GPIO.input(self.button_pin)  # Lire l'état actuel du bouton.
        # Détection de la transition de LOW à HIGH (bouton pressé).
        if current_state == GPIO.HIGH and self.last_state == GPIO.LOW and self._armed:
            # Pause pour éviter les rebonds.
            time.sleep(self.debounce_time)
            # Vérifie à nouveau si le bouton est toujours pressé.
            if GPIO.input(self.button_pin) == GPIO.HIGH:
                self.last_state = GPIO.HIGH
                self._armed = False
                return True
        elif current_state == GPIO.LOW:
            # Met à jour l'état précédent lorsque le bouton est relâché.
            self.last_state = GPIO.LOW
            # Ré-arme la détection après relâchement
            self._armed = True

        return False

    def cleanup(self):
        """
        Nettoie le GPIO du pin pour éviter les conflits après l'exécution du programme.
        """
        try:
            GPIO.remove_event_detect(self.button_pin)
        except Exception:
            pass
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
