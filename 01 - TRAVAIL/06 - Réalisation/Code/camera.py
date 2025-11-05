# camera.py
# Ce fichier gère la détection d'objets à partir de la caméra connectée à la Jetson Nano.
# Il utilise la bibliothèque Jetson Inference pour effectuer les détections et
# Jetson Utils pour capturer les images depuis la caméra.

from jetson_inference import detectNet
from jetson_utils import videoSource

class Camera:

    def __init__(self, model="ssd-mobilenet-v2", threshold=0.5, headless=True):
        """
        Initialise la caméra et le modèle de détection.
        :param model: Modèle utilisé pour détecter les objets (par défaut : "ssd-mobilenet-v2").
        :param threshold: Seuil minimum de confiance pour les détections.
        :param headless: Si True, désactive l'utilisation d'EGL/affichage (utile sans écran).
        """
        argv = ['--headless'] if headless else []
        self.net = detectNet(model, threshold=threshold, argv=argv)  # Charge le modèle de détection.
        # Source vidéo : caméra CSI (ou "/dev/video0" si nécessaire).
        # En mode headless, on passe l'argument pour éviter les erreurs EGL.
        self.camera = videoSource("csi://0", argv=argv)

    def get_detections(self):
        """
        Capture une image depuis la caméra et détecte les objets.
        :return: Une liste des objets détectés ou une liste vide si aucune image n'est capturée.
        """
        img = self.camera.Capture()  # Capture une image.
        if img is None:
            return []  # Si aucune image n'est capturée, retourne une liste vide.
        
        detections = self.net.Detect(img)  # Applique le modèle de détection sur l'image.
        return detections

    def get_class_name(self, class_id):
        """
        Récupère le nom d'une classe d'objet détectée à partir de son ID.
        :param class_id: L'ID de la classe d'objet détectée.
        :return: Le nom de la classe correspondante.
        """
        return self.net.GetClassDesc(class_id)

    def cleanup(self):
        """
        Libère les ressources utilisées par la caméra.
        """
        self.camera.Close()

if __name__ == "__main__":
    """
    Test de la caméra et des détections d'objets.
    Affiche dans le terminal les objets détectés avec leur niveau de confiance.
    """
    import time

    cam = Camera()  # Initialise la caméra avec le modèle par défaut.
    print("Test de la caméra")

    try:
        while True:
            # Récupère les objets détectés.
            detections = cam.get_detections()
            if detections:
                for detection in detections:
                    # Affiche le nom et la confiance pour chaque objet détecté.
                    class_name = cam.get_class_name(detection.ClassID)
                    confidence = detection.Confidence
                    print(f"Objet détecté : {class_name} avec confiance {confidence:.2f}")
            else:
                print("Aucun objet détecté.")
            time.sleep(1)  # Pause d'une seconde entre chaque détection.
    except KeyboardInterrupt:
        # Permet d'arrêter proprement le programme avec Ctrl + C.
        print("Programme interrompu.")
    finally:
        # Libère les ressources de la caméra à la fin.
        cam.cleanup()
