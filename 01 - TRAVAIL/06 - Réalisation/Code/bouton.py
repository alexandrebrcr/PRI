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
        :param button_pin: Numéro du GPIO auquel le bouton est connecté (mode BOARD).
        """
        self.button_pin = button_pin
        self.debounce_time = 0.1
        self._pressed_flag = False
        self.last_activation_time = 0.0

        # Configuration du GPIO en mode BOARD (numérotation physique des broches).
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # On initialise l'état précédent (devrait être HIGH au repos)
        time.sleep(0.02)
        self.last_state = GPIO.input(self.button_pin)

        # Détection d'événement sur front DESCENDANT (FALLING) : 1 -> 0
        try:
            GPIO.add_event_detect(
                self.button_pin,
                GPIO.FALLING,
                callback=self._on_press,
                bouncetime=int(self.debounce_time * 1000)
            )
            # Nettoyage des faux événements au démarrage
            GPIO.event_detected(self.button_pin)
            time.sleep(0.01)
        except Exception as e:
            print(f"Attention: Impossible d'activer la détection d'événements ({e}). Passage en mode polling.")
            pass

    def _on_press(self, channel):
        """
        Callback déclenché lors d'un front descendant (appui bouton).
        """
        # Anti-spam : on n'accepte pas de nouveaux événements trop rapprochés (0.3s)
        if time.time() - self.last_activation_time > 0.3:
             self._pressed_flag = True

    def wait_for_press(self):
        """
        Vérifie si le bouton a été pressé.
        Compatible avec la boucle principale de main.py.
        :return: True si un appui est détecté, sinon False.
        """
        # 1. Méthode par Interruption (Prioritaire)
        if self._pressed_flag:
            self._pressed_flag = False
            self.last_activation_time = time.time()
            self.last_state = GPIO.LOW 
            return True

        # 2. Méthode par Polling (Secours)
        current_state = GPIO.input(self.button_pin) 
        
        # Détection de transition : Était HIGH (Relâché) -> Devient LOW (Appuyé)
        if current_state == GPIO.LOW and self.last_state == GPIO.HIGH:
            
            # Vérification anti-spam
            if time.time() - self.last_activation_time > 0.3:
                # Anti-rebond logiciel sommaire
                time.sleep(self.debounce_time)
                
                # On vérifie si c'est toujours appuyé (LOW)
                if GPIO.input(self.button_pin) == GPIO.LOW:
                    self.last_state = GPIO.LOW
                    self.last_activation_time = time.time()
                    return True
        
        elif current_state == GPIO.HIGH:
            self.last_state = GPIO.HIGH

        return False

    def cleanup(self):
        """
        Nettoie le GPIO.
        """
        try:
            GPIO.remove_event_detect(self.button_pin)
        except Exception:
            pass
        GPIO.cleanup(self.button_pin)

if __name__ == "__main__":
    try:
        print("--- TEST BOUTON (Mode GND / Active Low) ---")
        print("Appuyez sur le bouton.")
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