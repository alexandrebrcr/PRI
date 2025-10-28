import cv2
import torch
import os
import time
from datetime import datetime
import requests

# Chemin vers le fichier wifi_logs.txt
wifi_config_file = "/home/projet_musee/wifi_logs.txt"

# Dossier de sortie
output_dir = "/home/projet_musee/Desktop/Image_comptage"
os.makedirs(output_dir, exist_ok=True)

# URL par défaut du serveur pour l'envoi des données
server_url = "https://visit-api.univ-tours.fr/visit-api/logs/record"

def read_config_from_logs(file_path):
    """
    Lit le fichier wifi_logs.txt et retourne le seuil de détection, l'intervalle de capture, l'URL du serveur, 
    le clientId et le nom de la Raspberry Pi.
    """
    detection_threshold = 0.3  # Seuil par défaut
    capture_interval = 30  # Intervalle par défaut
    custom_server_url = server_url  # URL par défaut
    client_id = "eed09916-bd76-4564-9dc4-5bf45d49b64a"  # ID par défaut
    raspberry_name = "RaspberryPi"  # Nom par défaut
    try:
        with open(file_path, "r") as file:
            for line in file:
                if line.startswith("Seuil_detection="):
                    detection_threshold = float(line.strip().split("=")[1])
                elif line.startswith("capture_intervalle="):
                    capture_interval = int(line.strip().split("=")[1])
                elif line.startswith("server_url="):
                    custom_server_url = line.strip().split("=")[1]
                elif line.startswith("clientId="):
                    client_id = line.strip().split("=")[1]
                elif line.startswith("NAME="):
                    raspberry_name = line.strip().split("=")[1]
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier wifi_logs.txt : {e}")
    return detection_threshold, capture_interval, custom_server_url, client_id, raspberry_name

def send_data_to_server(num_persons, custom_server_url, client_id, raspberry_name):
    """
    Envoie le nombre de personnes détectées au serveur avec le clientId et le nom de la Raspberry Pi.
    """
    try:
        payload = {
            "clientId": client_id,
            "logVersion": 5,
            "format": "csv",
            "records": [f"{raspberry_name};{datetime.now().isoformat()};{num_persons}"]
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(custom_server_url, json=payload, headers=headers)
        if response.status_code == 201:
            print("Données envoyées avec succès au serveur.")
        else:
            print(f"Échec de l'envoi des données. Code d'état : {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de l'envoi des données au serveur : {e}")

def capture_image():
    """
    Active la caméra, capture une image, puis l'éteint.
    """
    cap = cv2.VideoCapture(0)  # Utiliser la caméra par défaut
    if not cap.isOpened():
        print("Erreur : Impossible d'ouvrir la caméra.")
        return None

    ret, frame = cap.read()
    cap.release()  # Éteindre la caméra après capture
    if not ret:
        print("Erreur : Impossible de capturer une image.")
        return None

    return frame

def process_and_save_image(frame, detection_threshold, custom_server_url, client_id, raspberry_name):
    """
    Analyse l'image capturée, détecte les personnes et enregistre l'image avec le nombre de personnes détectées.
    """
    try:
        # Obtenir les dimensions de l'image
        height, width, _ = frame.shape

        # Analyse de l'image avec YOLO
        results = model(frame)
        detections = results.pandas().xyxy[0]  # Résultats sous forme de DataFrame

        # Compter les personnes détectées selon le seuil défini
        num_persons = sum(
            1 for _, row in detections.iterrows() if row['name'] == 'person' and row['confidence'] >= detection_threshold
        )

        # Générer un nom de fichier basé sur l'horodatage et le nombre de personnes détectées
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_persons_{num_persons}.jpg"
        output_path = os.path.join(output_dir, filename)

        # Enregistrer l'image annotée
        cv2.imwrite(output_path, frame)
        print(f"Image enregistrée : {output_path} | Nombre de personnes détectées : {num_persons}")

        # Envoyer les données au serveur
        send_data_to_server(num_persons, custom_server_url, client_id, raspberry_name)

    except Exception as e:
        print(f"Erreur lors du traitement de l'image : {e}")

def main():
    """
    Capture une image toutes les X secondes, analyse et enregistre les résultats.
    """
    global model

    # Lire le seuil de détection, l'intervalle de capture, l'URL du serveur, le clientId et le nom depuis wifi_logs.txt
    detection_threshold, capture_interval, custom_server_url, client_id, raspberry_name = read_config_from_logs(wifi_config_file)
    print(f"Seuil de détection configuré : {detection_threshold}")
    print(f"Intervalle de capture configuré : {capture_interval} secondes")
    print(f"URL du serveur configurée : {custom_server_url}")
    print(f"clientId configuré : {client_id}")
    print(f"Nom de la Raspberry Pi configuré : {raspberry_name}")

    # Charger le modèle YOLO
    model = torch.hub.load('/home/projet_musee/yolov5', 'custom', path='/home/projet_musee/yolov5/yolov5n.pt', source='local')

    while True:
        print("Capture de l'image...")
        frame = capture_image()  # Capture une image
        if frame is not None:
            process_and_save_image(frame, detection_threshold, custom_server_url, client_id, raspberry_name)  # Traite et sauvegarde l'image
        time.sleep(capture_interval)  # Pause avant la prochaine capture

if __name__ == "__main__":
    main()
