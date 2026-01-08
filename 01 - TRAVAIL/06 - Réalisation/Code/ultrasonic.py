# ultrasonic.py
# Ce fichier gère la communication avec un capteur ultrason via le port série

import serial 
import time
import threading

class UltrasonicSensor:

    def __init__(self, port="/dev/ttyTHS1", baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        
        # Variables partagées avec le thread
        self._latest_distance = None
        self._last_read_time = 0.0
        self._running = True # Pour arrêter le thread proprement
        
        # Anti-spam logs
        self._last_log = 0.0
        self._log_interval = 5.0

        # Connexion et Lancement du thread
        if self._open_serial():
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()

    def _log_throttled(self, msg: str):
        """Affiche un message au plus une fois toutes les _log_interval secondes."""
        now = time.time()
        if now - self._last_log >= self._log_interval:
            print(msg)
            self._last_log = now

    def _open_serial(self):
        """Essaie d'ouvrir le port série."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            return True
        except serial.SerialException as e:
            self._log_throttled(f"Erreur ouverture série ({self.port}) : {e}")
            return False

    def _read_loop(self):
        """
        Fonction qui tourne en arrière-plan (Thread) pour lire le capteur en continu.
        """
        while self._running:
            if not self.serial_conn or not self.serial_conn.is_open:
                time.sleep(1) # Attendre avant de réessayer
                self._open_serial()
                continue

            try:
                # Lecture bloquante de 1 octet pour trouver le Header (synchronisation)
                # On ne lit que si dispo ou on attend un peu, mais sans bloquer main.py
                if self.serial_conn.in_waiting > 0:
                    byte = self.serial_conn.read(1)
                    if len(byte) == 1 and byte[0] == 0xFF:
                        # Header trouvé ! On lit les 3 autres octets
                        data = self.serial_conn.read(3)
                        if len(data) == 3:
                            hi, lo, chksum = data[0], data[1], data[2]
                            checksum = (0xFF + hi + lo) & 0xFF
                            
                            if checksum == chksum:
                                distance_mm = (hi << 8) + lo
                                if distance_mm > 300: # Filtre bruit < 30cm
                                     self._latest_distance = distance_mm / 10.0 # cm
                                     self._last_read_time = time.time()
                else:
                    time.sleep(0.01) # Petite pause pour pas manger 100% CPU

            except Exception as e:
                self._log_throttled(f"Erreur thread ultrason : {e}")
                time.sleep(0.5)

    def get_distance(self):
        """
        Retourne instantanément la dernière distance valide connue.
        Retourne None si l'info est trop vieille (> 1 seconde).
        """
        if time.time() - self._last_read_time < 1.0:
            return self._latest_distance
        return None

    def cleanup(self):
        """Arrête le thread et ferme le port."""
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Capteur Ultrason arrêté.")

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
