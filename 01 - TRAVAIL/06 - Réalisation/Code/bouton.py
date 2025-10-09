import Jetson.GPIO as GPIO
import time

class Button:
	def __init__(self, button_pin=11):
		"""
		Initialisation du pin
		"""
		self.button_pin = button_pin
		self.last_state = GPIO.LOW
		self.debounce_time = 0.1
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

	def wait_for_press(self):
		"""
		attend une pression return true quand cest detectee
		"""
		current_state = GPIO.input(self.button_pin)
		if current_state == GPIO.HIGH and self.last_state == GPIO.LOW:
			time.sleep(self.debounce_time)
			if GPIO.input(self.button_pin) == GPIO.HIGH:
				self.last_state = GPIO.HIGH	
				return True
		elif current_state == GPIO.LOW:
			self.last_state = GPIO.LOW
		return False
	
	def cleanup(self):
		GPIO.cleanup(self.button_pin)


if __name__ == "__main__":
	try:
		# Correction: éviter la double assignation
		button = Button(button_pin=11)
		print("appuyer sur le boutton pour tester")
		while True:
			if button.wait_for_press():
				print("Bouton appuyé !")
				time.sleep(0.5)
	except KeyboardInterrupt:
		print("Programme arrêté par l'utilisateur")
	finally:
		button.cleanup()