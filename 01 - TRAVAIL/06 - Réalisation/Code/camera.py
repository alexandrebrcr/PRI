# camera.py
# Gestion de la caméra AI et de l'inférence
# Modèles supportés : SSD-Mobilenet-v2, SSD-Inception-v2

import time
from jetson_inference import detectNet
from jetson_utils import videoSource

class Camera:
    
    def __init__(self, model="ssd-inception-v2", threshold=0.5): #Ancien modèle: mobilnet
        # Argv --headless pour désactiver l'affichage graphique (GUI)
        argv = ['--headless']
        
        # 1. Chargement du réseau de neurones
        print(f"Chargement du modèle {model}...")
        self.net = detectNet(model, threshold=threshold, argv=argv)
        
        # 2. Ouverture de la caméra CSI (Raspberry Pi Camera v2)
        src_str = "csi://0"
        opt = argv + ["--input-width=1280", "--input-height=720", "--input-rate=30"]
        self.camera = videoSource(src_str, argv=opt)

        # 3. Dictionnaire de traduction COCO (91 classes)
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
        img = self.camera.Capture()
        if img is None:
            return []
        
        # Inférence (Détection)
        detections = self.net.Detect(img)
        return detections

    def clear_buffer(self):
        self.camera.Capture()

    def get_class_name(self, class_id):
        english_name = self.net.GetClassDesc(class_id)
        return self.translations.get(english_name.lower(), english_name)

    def get_object_position(self, detection):
        center_x = detection.Center[0]
        w = 1280
        
        if center_x < (w / 3):
            return "à gauche"
        elif center_x > (w * 2 / 3):
            return "à droite"
        else:
            return "devant"

    def cleanup(self):
        if self.camera:
            self.camera.Close()

# --- Test Unitaire ---
if __name__ == "__main__":
    print("--- TEST CAMERA ---")
    try:
        cam = Camera()
        print("Caméra initialisée. Début capture (CTRL+C pour arrêter)...")
        
        while True:
            t0 = time.time()
            dets = cam.get_detections()
            dt = time.time() - t0
            
            if dets:
                print(f"[{dt:.3f}s] {len(dets)} objets :")
                for d in dets:
                    name = cam.get_class_name(d.ClassID)
                    pos = cam.get_object_position(d)
                    conf = d.Confidence
                    print(f" - {name} ({pos}) [{conf:.2f}]")
            else:
                print(f"[{dt:.3f}s] Rien.")
                        
    except KeyboardInterrupt:
        pass
    finally:
        if 'cam' in locals(): cam.cleanup()
