import Jetson.GPIO as GPIO
import time

class Vibration:
	def __init__(self, vibration_pin=13):
		"""
		Initialisation avec le pin 13
		"""
		self.vibration_pin = vibration_pin
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.vibration_pin, GPIO.OUT, initial=GPIO.LOW)
		print(f"Vibreur configuré sur le pin {self.vibration_pin}")

	def vibrate(self, duration):
		"""
		Activation du vibreur pour une durée donnée
		"""
		print(f"Vibration activée pendant {duration} seconde(s).")
		GPIO.output(self.vibration_pin, GPIO.HIGH)
		time.sleep(duration)
		GPIO.output(self.vibration_pin, GPIO.LOW)

	def cleanup(self):
		"""
		Nettoie du GPIO après utilisation
		"""
		GPIO.cleanup(self.vibration_pin)
		print("GPIO du vibreur nettoyé")
	

if __name__ == "__main__":
	try:
		vibreur = Vibration(vibration_pin=13)
		print("Test du vibreur")
		while True:
			vibreur.vibrate(0.5)
			time.sleep(1)
	except KeyboardInterrupt:
		print("Existing program.")
	finally:
		vibreur.cleanup()

