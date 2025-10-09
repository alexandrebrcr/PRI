import time
from bouton import Button
from vibration import Vibration
from camera import Camera
from sound import Sound
from ultrasonic import UltrasonicSensor 

def format_distance_in_meters(distance): 
	# Protection contre None - AJOUTÉ POUR ÉVITER L'ERREUR
	if distance is None:
		return "inconnue"
	# Mettre la distance de base en centimètres sous forme mètres . centimètres (320cm -> 3.2)
	meters = distance / 100
	return f"{meters:.1f}"

def main():
	# Initialisation des composants
	button = Button(button_pin=11)
	vibration_motor = Vibration(vibration_pin=13)
	ultrasonic_sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)
	camera = Camera() 
	sound = Sound(script_path="./text_to_speech.sh") 

	# Definition des modes
	modes = ["exploration", "marche"]
	current_mode_index = 0
	current_mode = modes[current_mode_index]
	sound.speak("Le système a démarré")

	# Annonce du mode actuel
	sound.speak(f"Mode {current_mode}")
	print(f"Mode {current_mode}")
	
	try:
		while True:
			# Gestion du bouton pour changer du mode
			if button.wait_for_press():
				current_mode_index = (current_mode_index + 1) % len(modes)
				current_mode = modes[current_mode_index]
				sound.speak(f"Mode {current_mode}")
				print(f"Mode {current_mode}")
			
			# Mode exploration : caméra + capteur ultrason 
			if current_mode == "exploration":
				detections = camera.get_detections()
				distance = ultrasonic_sensor.get_distance()
				
				# Afficher la distance si disponible
				if distance is not None:
					print(f"{distance} centimètres")
				
				if detections:
					for detection in detections:
						formatted_distance = format_distance_in_meters(distance)
						class_name = camera.get_class_name(detection.ClassID)
						confidence = detection.Confidence
						sound.speak(f" {class_name} à {formatted_distance}")
						print(f" {class_name} à {formatted_distance}")
				else:
					# Correction orthographe
					sound.speak("Aucun objet détecté")
					print("Aucun objet détecté")

			# Mode marche 
			elif current_mode == "marche":
				distance = ultrasonic_sensor.get_distance()
				
				# PROTECTION CONTRE DISTANCE=NONE
				if distance is not None:
					formatted_distance = format_distance_in_meters(distance)
					print(f"{distance} centimètres")
					
					if 400 <= distance <= 500:
						sound.speak(f"{formatted_distance}")
						#vibration_motor.vibrate(0.25)
						#time.sleep(0.25)
					elif 300 <= distance <= 400:
						sound.speak(f"{formatted_distance}")
						"""vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)"""
					elif 200 <= distance <= 300:
						sound.speak(f"{formatted_distance}")
						"""vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)"""
					elif distance < 200:
						sound.speak(f"{formatted_distance}")
						"""vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)
						vibration_motor.vibrate(0.25)
						time.sleep(0.25)"""
					else:
						sound.speak("Rien")
						#sound.speak(f"{formatted_distance}")
						time.sleep(0.25)
				else:
					sound.speak("Distance non disponible")

			# Petite pause pour réduire CPU
			time.sleep(0.01)

	except KeyboardInterrupt:
		print("Programme arrêté par l'utilisateur")
	finally:
		# Nettoyage des GPIO et ressources
		button.cleanup()
		vibration_motor.cleanup()
		ultrasonic_sensor.cleanup()
		print("Nettoyage complet")				 


if __name__ == "__main__":
	main()