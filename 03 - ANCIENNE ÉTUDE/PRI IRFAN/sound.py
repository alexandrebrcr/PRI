# sound.py
# Ce fichier gère la synthèse vocale à l'aide d'un script shell externe.
# Il permet de convertir du texte en parole en appelant le script `text_to_speech.sh`.

import os

class Sound:

    def __init__(self, script_path="./text_to_speech.sh"):
        """
        Initialise la classe avec le chemin du script shell.
        :param script_path: Chemin vers le script utilisé pour la synthèse vocale.
        """
        self.script_path = script_path  # Chemin du script `text_to_speech.sh`.

    def speak(self, text):
        """
        Convertit un texte en parole en appelant le script shell.
        :param text: Le texte à convertir en parole.
        """
        try:
            # Appelle le script shell avec le texte en paramètre.
            os.system(f"{self.script_path} \"{text}\"")
        except Exception as e:
            # Gère les erreurs liées à la synthèse vocale.
            print(f"Erreur de la synthèse vocale : {e}")

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
    except Exception as e:
        print(f"Erreur dans le test : {e}")
