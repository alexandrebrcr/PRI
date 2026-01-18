# camera.py
# Ce fichier gère la détection d'objets à partir de la caméra connectée à la Jetson Nano.
# Il utilise la bibliothèque Jetson Inference pour effectuer les détections et
# Jetson Utils pour capturer les images depuis la caméra.

from jetson_inference import detectNet
from jetson_utils import videoSource

class Camera:

    def __init__(self, model="ssd-inception-v2", threshold=0.5): #mobilenet
        """
        Initialise la caméra et le modèle de détection.
        :param model: Modèle utilisé pour détecter les objets (par défaut : "ssd-mobilenet-v2").
        :param threshold: Seuil minimum de confiance pour les détections.
        """
        # Argv --headless permet de lancer le script sans interface graphique
        argv = ['--headless']
        self.net = detectNet(model, threshold=threshold, argv=argv)
        
        # Ajout de --input-flip=rotate-180 pour corriger la caméra à l'envers
        self.camera = videoSource("csi://0", argv=argv + ["--input-width=1280", "--input-height=720", "--input-rate=30"])

        # Dictionnaire de traduction Anglais -> Français pour le dataset COCO (91 classes)
        self.translations = {
            "person": "personne", "bicycle": "vélo", "car": "voiture", "motorcycle": "moto",
            "airplane": "avion", "bus": "bus", "train": "train", "truck": "camion", "boat": "bateau",
            "traffic light": "feu tricolore", "fire hydrant": "bouche incendie", "stop sign": "panneau stop",
            "bench": "banc", "bird": "oiseau", "cat": "chat", "dog": "chien", "backpack": "sac à dos",
            "umbrella": "parapluie", "handbag": "sac à main", "tie": "cravate", "suitcase": "valise",
            "bottle": "bouteille", "wine glass": "verre de vin", "cup": "tasse", "fork": "fourchette",
            "knife": "couteau", "spoon": "cuillère", "bowl": "bol", "banana": "banane", "apple": "pomme",
            "sandwich": "sandwich", "orange": "orange", "broccoli": "brocoli", "carrot": "carotte",
            "chair": "chaise", "couch": "canapé", "potted plant": "plante", "bed": "lit",
            "dining table": "table", "toilet": "toilettes", "tv": "télé", "laptop": "ordinateur",
            "mouse": "souris", "remote": "télécommande", "keyboard": "clavier", "cell phone": "téléphone",
            "microwave": "micro-ondes", "oven": "four", "sink": "évier", "refrigerator": "frigo",
            "book": "livre", "clock": "horloge", "vase": "vase", "scissors": "ciseaux",
            "teddy bear": "ours en peluche", "hair drier": "sèche-cheveux", "toothbrush": "brosse à dents"
        }

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
        :return: Le nom de la classe correspondante (traduit en français si possible).
        """
        english_name = self.net.GetClassDesc(class_id)
        # On retourne la traduction si elle existe, sinon le nom anglais original
        return self.translations.get(english_name.lower(), english_name)

    def get_object_position(self, detection):
        """
        Détermine la position horizontale de l'objet dans l'image (1280px de large).
        :param detection: Objet detection renvoyé par jetson_inference
        :return: "à gauche", "à droite" ou "devant"
        """
        center_x = detection.Center[0]
        width = 1280 # Largeur définie dans le constructeur
        
        # On découpe l'image en 3 tiers
        if center_x < (width / 3):
            return "à gauche"
        elif center_x > (width * 2 / 3):
            return "à droite"
        else:
            return "devant"

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
