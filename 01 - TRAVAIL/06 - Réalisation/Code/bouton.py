# bouton.py
# Gestion du bouton poussoir (GPIO 11) - Optimisé Interruptions

import Jetson.GPIO as GPIO
import time

class Button:
    def __init__(self, button_pin=11):
        self.button_pin = button_pin
        self.pressed_flag = False
        self.last_press_time = 0.0
        self.debounce = 0.3
        self.interrupt_mode = False

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            # Mode optimisé : Le système nous réveille quand on appuie
            GPIO.add_event_detect(self.button_pin, GPIO.FALLING, 
                                callback=self._callback, bouncetime=200)
            self.interrupt_mode = True
        except:
            pass # Fallback polling silencieux
        
        self.last_state = GPIO.input(self.button_pin)

    def _callback(self, channel):
        if time.time() - self.last_press_time > self.debounce:
             self.pressed_flag = True
             self.last_press_time = time.time()

    def wait_for_press(self):
        # 1. Interruption (Rapide)
        if self.interrupt_mode:
            if self.pressed_flag:
                self.pressed_flag = False
                return True
            return False

        # 2. Polling (Secours)
        curr = GPIO.input(self.button_pin)
        if curr == GPIO.LOW and self.last_state == GPIO.HIGH:
            now = time.time()
            if now - self.last_press_time > self.debounce:
                time.sleep(0.05)
                if GPIO.input(self.button_pin) == GPIO.LOW:
                    self.last_press_time = now; self.last_state = GPIO.LOW
                    return True
        self.last_state = curr
        return False

    def cleanup(self):
        try: GPIO.remove_event_detect(self.button_pin)
        except: pass
        GPIO.cleanup(self.button_pin)
