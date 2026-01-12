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
        
        # CORRECTION AUTOMATIQUE DES PERMISSIONS
        # Rend le script exécutable (chmod +x) pour éviter l'erreur [Errno 13] Permission denied
        if os.path.exists(self.script_path):
            try:
                os.chmod(self.script_path, 0o755)
            except Exception as e:
                print(f"Attention: Impossible de changer les permissions du script son ({e})")

        self._queue_normal = Queue(maxsize=queue_size)
        self._queue_priority = Queue(maxsize=queue_size)
        self._stop = False
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

    def _run_worker(self):
        """Boucle du worker qui consomme les messages TTS."""
        while not self._stop:
            text = None
            
            # 1. On vérifie d'abord la file PRIORITAIRE (non-bloquant)
            if not self._queue_priority.empty():
                try:
                    text = self._queue_priority.get_nowait()
                    self._queue_priority.task_done()
                except Empty:
                    pass
            
            # 2. Si rien en prioritaire, on regarde la file NORMALE (ou blocage court)
            if text is None:
                try:
                    # Timeout court pour vérifier régulièrement si un message prioritaire arrive
                    text = self._queue_normal.get(timeout=0.1)
                    self._queue_normal.task_done()
                except Empty:
                    continue
            
            # 3. Traitement du message (Identique)
            if text is None:
                continue

            try:
                # Exécution synchrone du script
                import gc
                gc.collect()
                subprocess.run([self.script_path, text], check=False)
            except OSError as e:
                 if e.errno == 12:
                     print("Erreur mémoire TTS (récupération...)")
                     time.sleep(1)
            except Exception as e:
                print(f"Erreur TTS : {e}")

    def speak(self, text, priority=False):
        """
        Enfile un texte pour synthèse vocale.
        :param priority: Si True, le message est mis dans une file prioritaire et ne peut pas être écrasé.
                         Si False, le message écrase les précédents messages normaux en attente.
        """
        if priority:
            # Message important (Mode, Alerte système) : On l'ajoute à la file prioritaire
            # On ne vide PAS la file prioritaire, on empile les messages importants
            try:
                self._queue_priority.put_nowait(text)
            except Full:
                pass
        else:
            # Message 'spam' (Distance, Objet) : On vide la file NORMALE pour ne garder que le frais
            try:
                while not self._queue_normal.empty():
                    try:
                        self._queue_normal.get_nowait()
                        self._queue_normal.task_done()
                    except Empty:
                        break
                
                self._queue_normal.put_nowait(text)
            except Full:
                pass

    def cleanup(self, drain_timeout=2.0):
        """Arrête proprement le worker TTS."""
        self._stop = True
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
