import os
import time
import subprocess

class Sound:
	def __init__(self, script_path="./text_to_speech.sh"):
		self.script_path = script_path
		self.last_speak_time = 0
		self.last_message = ""
		self.min_interval = 1.5  # Intervalle minimum entre deux messages (1.5 sec)
		
	def speak(self, text):
		current_time = time.time()
		
		# Anti-spam: ne pas répéter le même message en moins de 2 secondes
		if text == self.last_message and current_time - self.last_speak_time < 2.0:
			return
			
		# Cooldown général: attendre au moins min_interval entre les messages
		if current_time - self.last_speak_time < self.min_interval:
			return
			
		try:
			# Utiliser subprocess au lieu de os.system (plus sécurisé)
			subprocess.run([self.script_path, text], check=False)
			self.last_speak_time = current_time
			self.last_message = text
		except Exception as e:
			print(f"Erreur de la synthèse vocale : {e}")