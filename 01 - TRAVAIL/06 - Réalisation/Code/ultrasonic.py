# ultrasonic.py
# Ce fichier gère la communication avec un capteur ultrason via le port série

import serial 
import time    

class UltrasonicSensor:

    def __init__(self, port="/dev/ttyTHS1", baudrate=9600, timeout=1):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        # Anti-spam pour logs
        self._last_log = 0.0
        self._log_interval = 5.0  # secondes
        # Tentative d'ouverture initiale
        self._open_serial()

    def _log_throttled(self, msg: str):
        """Affiche un message au plus une fois toutes les _log_interval secondes."""
        now = time.time()
        if now - self._last_log >= self._log_interval:
            print(msg)
            self._last_log = now

    def _open_serial(self):
        """Essaie d'ouvrir le port série si fermé, avec gestion des permissions."""
        if self.serial_conn and getattr(self.serial_conn, "is_open", False):
            return True
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            return True
        except serial.SerialException as e:
            # Log limité pour éviter le spam
            self._log_throttled(f"Erreur ouverture série ({self.port}) : {e}")
            self.serial_conn = None
            return False

    def get_distance(self):
        """
        Lit les données du capteur et retourne la distance mesurée.
        :return: Distance en centimètres ou None en cas d'erreur.
        """
        # Vérifie si la connexion série est disponible
        if not self.serial_conn or not self.serial_conn.is_open:
            # Tente une réouverture silencieuse
            if not self._open_serial():
                return None

        try:
            # Vider le buffer d'entrée pour éviter l'accumulation
            self.serial_conn.reset_input_buffer()

            # Lecture des 4 octets du capteur (retourne < 4 si timeout)
            data = self.serial_conn.read(4)
            if len(data) != 4:
                return None

            # Vérification des données reçues
            hdr, hi, lo, chksum = data[0], data[1], data[2], data[3]
            if hdr != 0xFF:
                return None

            checksum = (hdr + hi + lo) & 0xFF
            if checksum != chksum:
                # Checksum invalide
                return None

            distance = (hi << 8) + lo  # en mm si capteur type JSN-SR04T série (ex.)
            if distance > 30:  # Ignore < 30 (bruit/proximité capteur)
                return distance / 10  # conversion en cm
            else:
                return None
        except Exception as e:
            # Gestion des erreurs lors de la lecture des données.
            self._log_throttled(f"Erreur lecture données ultrason : {e}")
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
