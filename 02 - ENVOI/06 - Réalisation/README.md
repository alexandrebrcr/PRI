# Projet Canne Blanche Intelligente

**Auteur :** Alexandre BOURCIER

**Encadrant :** Gilles Venturini

**Contexte :** Projet de Recherche et d'Ingénierie (PRI) - Polytech Tours 5A

## 1. Description du Projet

Ce système est une aide à la navigation pour personnes malvoyantes embarquée sur une carte NVIDIA Jetson Nano. Il combine plusieurs modes de fonctionnement pour assister l'utilisateur :

1.  **Mode Marche** : Détection d'obstacles par ultrasons.
2.  **Mode Exploration** : Reconnaissance d'objets par caméra.
3.  **Mode Mixte** : Combinaison des ultrasons et de la caméra.

## 2. Démarrage Automatique

Le système est configuré pour démarrer automatiquement à l'alimentation de la carte Jetson Nano.

Le programme principal est exécuté en tant que service système (`systemd`). Tout le code source et les scripts se trouvent dans le répertoire suivant sur la carte cible :

`/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code`

Si le programme plante, le service est configuré pour tenter un redémarrage automatique toutes les 30s.

## 3. Installation et Initialisation sur une Nouvelle Carte

Voici la procédure détaillée pour déployer le système sur une nouvelle carte Jetson Nano vierge (ou réinitialisée).

### Prérequis
*   Une Jetson Nano configurée avec l'OS officiel.
*   Un utilisateur nommé `canneblancheintelligente` (recommandé pour correspondre aux chemins du service).
*   Mot de passe (par défaut sur ce projet) : `canneblanche`.

### Étape 1 : Copie des Fichiers
Transférez l'intégralité du dossier Code dans l'arborescence de l'utilisateur. Pour respecter la configuration actuelle du service, le chemin absolu doit être :
`/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code`

Si vous changez ce chemin, vous devrez modifier les fichiers `canne_intelligente.service` et `startup_script.sh` pour mettre à jour les chemins (`WorkingDirectory` et `PROJECT_DIR`).

### Étape 2 : Permissions des Scripts
Rendez le script de démarrage exécutable :

```bash
cd "/home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code"
chmod +x startup_script.sh
```

### Étape 3 : Configuration du Port Série (Ultrasons)
Le capteur ultrason utilise le port `/dev/ttyTHS1`. Le script de démarrage tente de régler les droits automatiquement, mais il est préférable de s'assurer que l'utilisateur a accès au groupe `dialout` :

```bash
sudo usermod -a -G dialout `$USER
```
*(Un redémarrage est nécessaire pour que cela prenne effet).*

Le script `startup_script.sh` contient également une commande de secours `sudo chmod 666 /dev/ttyTHS1` exécutée au lancement.

### Étape 4 : Installation et Activation du Service Systemd

Le fichier `canne_intelligente.service` décrit comment le système doit démarrer.

1.  **Copier le fichier de service** dans le répertoire système :
    ```bash
    sudo cp canne_intelligente.service /etc/systemd/system/
    ```

2.  **Recharger le démon systemd** pour qu'il prenne en compte le nouveau fichier :
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Activer le service** pour qu'il se lance au démarrage du système (boot) :
    ```bash
    sudo systemctl enable canne_intelligente.service
    ```

4.  **Démarrer le service manuellement** (pour tester immédiatement sans redémarrer) :
    ```bash
    sudo systemctl start canne_intelligente.service
    ```

### Étape 5 : Vérification et Maintenance

Pour vérifier que le service tourne correctement :
```bash
sudo systemctl status canne_intelligente.service
```

Pour voir les logs (sorties print du python ou erreurs) :
```bash
journalctl -u canne_intelligente.service -f
```

Pour arrêter le service (afin de lancer `main.py` manuellement par exemple) :
```bash
sudo systemctl stop canne_intelligente.service
```

## 4. Lancement Manuel

Si vous avez besoin de lancer le programme manuellement pour le débogage :

1.  Stoppez le service automatique : `sudo systemctl stop canne_intelligente.service`
2.  Allez dans le dossier : `cd /home/canneblancheintelligente/Documents/PRI_ALEXANDRE/PRI/01 - TRAVAIL/06 - Réalisation/Code`
3.  Activez les droits sur le port série (si pas déjà fait) : `sudo chmod 666 /dev/ttyTHS1`
4.  Lancez le main : `python3 main.py`