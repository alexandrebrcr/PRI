from jetson_inference import detectNet
from jetson_utils import videoSource

class Camera:
	def __init__(self, model="ssd-mobilenet-v2", threshold=0.5):
		self.net = detectNet(model, threshold=threshold)
		self.camera = videoSource("csi://0") # utiliser "/dev/video0" si nécessaire

	def get_detections(self):
		img = self.camera.Capture()
		if img is None:
			return [] 	
		detections = self.net.Detect(img)
		return detections

	def get_class_name(self, class_id):
		# recup le nom de la classe d'un id
		return self.net.GetClassDesc(class_id)

	def cleanup(self):
		self.camera.Close()

if __name__ == "__main__":
	import time
	
	cam = Camera()
	print("Test de la caméra")
	
	try:
		while True:
			detections = cam.get_detections()
			if detections:
				for detection in detections:
					class_name = cam.get_class_name(detection.ClassID)
					confidence = detection.Confidence
					print(f"Objet détecté : {class_name} avec confiance {confidence:.2f}")
			else:
				print("Aucun objet détecté.")
			time.sleep(1)
	except KeyboardInterrupt:
		print("Programme interrompu.")
	finally:
		cam.cleanup()

