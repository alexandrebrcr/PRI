import serial
import time

class UltrasonicSensor:
	def __init__(self, port="/dev/ttyTHS1", baudrate=9600, timeout=1):
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout
		try:
			self.serial_conn = serial.Serial(
				port=self.port,
				baudrate=self.baudrate,
				timeout=self.timeout
			)
		except serial.SerialException as e:
			print(f"Erreur init : {e}")
			self.serial_conn = None

	def get_distance(self):
		if not self.serial_conn or not self.serial_conn.is_open:
			print("Connexion serie non disponible")
			return None

		try:
			
			# Vider le buffer serie avant de lire les données pour éviter les problemes
			self.serial_conn.reset_input_buffer()

			data = []
			# Lecture des 4 octets
			while len(data) < 4:
				byte = self.serial_conn.read()
				if byte:
					data.append(byte)				
	
			# Verification des données
			if data[0] == b'\xff':
				checksum = (data[0][0] + data[1][0] + data[2][0]) & 0xFF
				if checksum == data[3][0]:
					distance = (data[1][0] << 8) + data[2][0]
					if distance > 30:
						return distance / 10
					else:
						print("En-dessous de la limite inférieure.")
						return None
				else:
					print("Erreur : Checksum invalide.")
					return None
			else:
				print("Erreur : Données invalides.")
				return None
		except Exception as e:
			print(f"Erreur lors de la lecture des données : {e}")
			return None

	def cleanup(self):
		# Correction: Logique inversée dans la condition
		if self.serial_conn and self.serial_conn.is_open:
			self.serial_conn.close()
			print("connexion serie fermée proprement")
			

if __name__ == "__main__":
	try:
		sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)
		while True:
			distance_cm = sensor.get_distance()
			if distance_cm:
				print(f"distance mesurée : {distance_cm:.1f} cm")
			else:
				print("Erreur lors de la mesure")
			time.sleep(1)
	except KeyboardInterrupt:
		print("Programme arreter par le user")
	finally:
		sensor.cleanup()