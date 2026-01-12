import sys
from jetson_inference import detectNet
from jetson_utils import videoSource, videoOutput

# Pour quitter : Ctrl+C dans le terminal ou fermez la fenêtre

def main():
    print("Initialisation de la caméra et de l'affichage...")
    
    # 1. Modèle de détection (le même que dans votre projet)
    # Si 'ssd-inception-v2' est trop lourd pour le test, remplacez par 'ssd-mobilenet-v2'
    net = detectNet("ssd-inception-v2", threshold=0.5)

    # 2. Source vidéo
    # On teste d'abord SANS la rotation qui fait planter
    camera = videoSource("csi://0", argv=[
        "--input-width=1280", 
        "--input-height=720", 
        "--input-rate=30"
    ])

    # 3. Sortie vidéo (Fenêtre sur l'écran HDMI connecté à la Jetson)
    display = videoOutput("display://0")

    print("Démarrage du flux...")

    while display.IsStreaming():
        # Capture de l'image
        img = camera.Capture()
        
        if img is None:
            continue

        # Détection
        # overlay="box,labels,conf" dessine les cadres, les noms et les % de confiance
        detections = net.Detect(img, overlay="box,labels,conf")

        # Affichage
        display.Render(img)

        # Mise à jour du titre de la fenêtre avec le nombre d'images/seconde
        display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt utilisateur.")
    except Exception as e:
        print(f"\nErreur critique : {e}")
