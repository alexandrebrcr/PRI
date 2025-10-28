# sound.py
# Ce fichier gère la synthèse vocale à l'aide d'un script shell externe.
# Il permet de convertir du texte en parole en appelant le script `text_to_speech.sh`.

import os
import threading
import subprocess
from queue import Queue, Full, Empty
import time

class Sound:

    def __init__(self, script_path="./text_to_speech.sh", queue_size=10):
        """
        Initialise la classe avec un worker asynchrone pour la TTS.
        :param script_path: Chemin vers le script utilisé pour la synthèse vocale.
        :param queue_size: Taille max de la file d'attente de messages TTS.
        """
        self.script_path = script_path  # Chemin du script `text_to_speech.sh`.
        self._queue = Queue(maxsize=queue_size)
        self._stop = False
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    def _run_worker(self):
        """Boucle du worker qui consomme les messages TTS de manière séquentielle."""
        while not self._stop:
            try:
                item = self._queue.get(timeout=0.25)
            except Empty:
                continue
            if item is None:
                # Sentinel pour arrêter le worker
                break
            text = item
            try:
                # Exécution synchrone du script pour éviter des lectures audio en parallèle.
                subprocess.run([self.script_path, text], check=False)
            except Exception as e:
                print(f"Erreur de la synthèse vocale : {e}")
            finally:
                self._queue.task_done()

    def speak(self, text):
        """
        Enfile un texte pour synthèse vocale sans bloquer la boucle principale.
        :param text: Le texte à convertir en parole.
        """
        try:
            self._queue.put_nowait(text)
        except Full:
            # File pleine: on ignore ce message pour éviter la saturation audio.
            pass

    def cleanup(self, drain_timeout=2.0):
        """Arrête proprement le worker TTS et vide la file autant que possible."""
        # Optionnel: attendre un court instant que la file se vide
        end_time = time.time() + drain_timeout
        while not self._queue.empty() and time.time() < end_time:
            time.sleep(0.05)
        self._stop = True
        try:
            self._queue.put_nowait(None)  # Sentinel
        except Full:
            pass
        if self._worker.is_alive():
            self._worker.join(timeout=2.0)

# Exemple d'utilisation
if __name__ == "__main__":
    """
    Test de la synthèse vocale en mode autonome.
    Permet de tester rapidement si le script shell fonctionne correctement.
    """
    try:
        # Initialisation de la classe Sound avec le chemin par défaut du script.
        sound = Sound()
        print("Test de la synthèse vocale :")
        
        # Exemple de texte à convertir en parole.
        test_text = "Bonjour, ceci est un test ."
        sound.speak(test_text)
        time.sleep(2)
        sound.cleanup()
    except Exception as e:
        print(f"Erreur dans le test : {e}")
