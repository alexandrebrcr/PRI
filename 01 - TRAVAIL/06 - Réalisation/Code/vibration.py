# vibration.py
# Ce fichier gère le vibreur

import Jetson.GPIO as GPIO
import time
import threading

class Vibration:

    def __init__(self, vibration_pin=13):
        """Initialisation du vibreur"""
        self.vibration_pin = vibration_pin  
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.vibration_pin, GPIO.OUT, initial=GPIO.LOW)
        self._current_thread = None

    def vibrate(self, duration):
        """
        Lance une vibration de 'duration' secondes en arrière-plan.
        Ne bloque PAS l'exécution du programme principal.
        """
        # Si ça vibre déjà, on ignore la nouvelle demande pour ne pas 'empiler' les threads
        if self._current_thread is not None and self._current_thread.is_alive():
            return

        # On lance le travail dans un thread séparé
        self._current_thread = threading.Thread(
            target=self._vibrate_worker, 
            args=(duration,), 
            daemon=True
        )
        self._current_thread.start()

    def _vibrate_worker(self, duration):
        """La tâche réelle qui s'exécute en parallèle"""
        try:
            GPIO.output(self.vibration_pin, GPIO.HIGH)
            time.sleep(duration) 
        finally:
            GPIO.output(self.vibration_pin, GPIO.LOW)

    def cleanup(self):
        """Nettoie le GPIO proprement"""
        try:
            # On s'assure que le vibreur est éteint
            GPIO.output(self.vibration_pin, GPIO.LOW)
            if self._current_thread and self._current_thread.is_alive():
                self._current_thread.join(timeout=0.5)
        except Exception:
            pass
        GPIO.cleanup(self.vibration_pin)
        print("GPIO Vibreur libéré.")

if __name__ == "__main__":
    v = Vibration()
    print("Test de la vibration.")
    v.vibrate(2.0)
    print("Ce message doit Apparaitre AVANT la fin de la vibration !)")
    time.sleep(3)
    v.cleanup()
