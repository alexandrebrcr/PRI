# ultrasonic.py
# Ce fichier gère la communication avec un capteur ultrason via le port série

import serial 
import time    

class UltrasonicSensor:

    def __init__(self, port="/dev/ttyTHS1", baudrate=9600, timeout=1):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        try:
            # Initialisation de la connexion série
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
        except serial.SerialException as e:
            # Gestion des erreurs lors de l'initialisation
            print(f"Erreur init : {e}")
            self.serial_conn = None

    def get_distance(self):
        """
        Lit les données du capteur et retourne la distance mesurée.
        :return: Distance en centimètres ou None en cas d'erreur.
        """
        # Vérifie si la connexion série est disponible
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Connexion série non disponible")
            return None

        try:
            # Vider le buffer série pour éviter le blocage des données reçues
            self.serial_conn.reset_input_buffer()

            # Lire les 4 octets envoyés par le capteur
            data = []
            while len(data) < 4:
                byte = self.serial_conn.read()
                if byte:
                    data.append(byte)

            # Vérification des données reçues
            if data[0] == b'\xff':  # Premier octet doit être 0xFF
                checksum = (data[0][0] + data[1][0] + data[2][0]) & 0xFF
                if checksum == data[3][0]:  # Vérification du checksum
                    distance = (data[1][0] << 8) + data[2][0]  # Calcul de la distance
                    if distance > 30:  # Ignore les distances en dessous de 30 cm
                        return distance / 10  # Retourne la distance en cm
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
            # Gestion des erreurs lors de la lecture des données.
            print(f"Erreur lors de la lecture des données : {e}")
            return None

    def cleanup(self):
        """
        Ferme proprement la connexion série.
        """
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Connexion série fermée proprement.")

# Exemple d'utilisation
if __name__ == "__main__":
    """
    Test du capteur ultrason.
    Mesure et affiche la distance dans le terminal toutes les secondes.
    """
    try:
        # Initialisation du capteur sur le port série spécifié.
        sensor = UltrasonicSensor(port="/dev/ttyTHS1", baudrate=9600)
        while True:
            # Lecture et affichage de la distance.
            distance_cm = sensor.get_distance()
            if distance_cm:
                print(f"Distance mesurée : {distance_cm:.1f} cm")
            else:
                print("Erreur lors de la mesure")
            time.sleep(1)
    except KeyboardInterrupt:
        # Arrêt propre en cas d'interruption par l'utilisateur (Ctrl + C)
        print("Programme arrêté par l'utilisateur.")
    finally:
        # Nettoyage des ressources série
        sensor.cleanup()
