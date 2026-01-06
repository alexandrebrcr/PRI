# bouton.py
# Ce fichier permet de gérer les appuis d'un bouton poussoir connecter au GPIO de la Jetson Nano sur le pin 11.
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
        self.last_state = GPIO.LOW  # État précédent du bouton (pour fallback).
        self.debounce_time = 0.1  # Temps de rebond pour éviter les détections multiples.
        self._pressed_flag = False  # Indique qu'un front montant a été détecté.
        self.last_activation_time = 0.0 # Timestamp de la dernière activation validée

        # Configuration du GPIO en mode BOARD (numérotation physique des broches).
        GPIO.setmode(GPIO.BOARD)

        # Configuration du pin du bouton en entrée avec pull-down.
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Initialiser l'état précédent à partir de l'état réel de la broche
        # pour éviter une fausse transition lors du premier cycle.
        time.sleep(0.02)
        self.last_state = GPIO.input(self.button_pin)

        # Détection d'événement sur front montant pour éviter le polling constant.
        try:
            GPIO.add_event_detect(
                self.button_pin,
                GPIO.RISING,
                callback=self._on_press,
                bouncetime=int(self.debounce_time * 1000)
            )
            # Vider un éventuel événement déjà en file (bruit au démarrage)
            GPIO.event_detected(self.button_pin)
            time.sleep(0.01)
            GPIO.event_detected(self.button_pin)
        except Exception as e:
            # Affiche l'erreur si l'événement n'est pas disponible
            print(f"Attention: Impossible d'activer la détection d'événements ({e}). Passage en mode polling.")
            pass

    def _on_press(self, channel):
        """
        Callback déclenché lors d'un front montant (appui bouton).
        """
        # Anti-spam : on n'accepte pas de nouveaux événements trop rapprochés (0.3s)
        # Cela filtre les rebonds au relâchement qui passeraient à travers le filtre hardware.
        if time.time() - self.last_activation_time > 0.3:
             self._pressed_flag = True

    def wait_for_press(self):
        """
        Vérifie si le bouton a été pressé en évitant les rebonds.
        :return: True si un appui est détecté, sinon False.
        """
        # Si un événement a été détecté, consommer le flag et retourner True
        if self._pressed_flag:
            self._pressed_flag = False
            self.last_activation_time = time.time() # Met à jour le timestamp
            
            # IMPORTANT : on met à jour last_state pour éviter que la logique de polling
            # ci-dessous ne détecte ce même appui une deuxième fois si le bouton est encore enfoncé.
            self.last_state = GPIO.HIGH
            return True

        # Fallback par polling si add_event_detect n'a pas pu être configuré
        current_state = GPIO.input(self.button_pin)  # Lire l'état actuel du bouton.
        # Détection de la transition de LOW à HIGH (bouton pressé).
        if current_state == GPIO.HIGH and self.last_state == GPIO.LOW:
            # Vérification anti-spam logicielle aussi pour le polling
            if time.time() - self.last_activation_time > 0.3:
                # Pause pour éviter les rebonds.
                time.sleep(self.debounce_time)
                # Vérifie à nouveau si le bouton est toujours pressé.
                if GPIO.input(self.button_pin) == GPIO.HIGH:
                    self.last_state = GPIO.HIGH
                    self.last_activation_time = time.time()
                    return True
        elif current_state == GPIO.LOW:
            # Met à jour l'état précédent lorsque le bouton est relâché.
            self.last_state = GPIO.LOW

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
