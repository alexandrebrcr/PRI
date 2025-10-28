# README

Ce fichier explique comment lancer le programme principal `main.py` sur la Jetson Nano.

////////////////////////////////////////////////////////////

Alimenter la Jeton nano, y brancher un clavier, une souris et un écran.

////////////////////////////////////////////////////////////

Mot de passe de la Jetson Nano : canneblanche

////////////////////////////////////////////////////////////

Une fois dans le bureau : 

- aller dans les fichiers -> dans Documents -> puis dans PRI_IRFAN

- Ouvrez un terminal depuis cet emplacement : clic droit " ouvrir un terminal " 

- Tapez la commande " sudo chmod 666 /dev/ttyTHS1 " qui sert a donner les droits au port THS1 pour le capteur à ultrason

- Lancer le script ultrasonic.py pendant quelques secondes " python ultrasonic.py " attendez jusqu'à que vous voyez les valeurs du capteur à ultrason puis faite ctrl + c pour quitter le programme 

- Ensuite lancer le main.py avec " python main.py " ensuite le programme prendra un peu de temps à se lancer.


# Des fois quelques problèmes peuvent survenir il suffit de relancer le programme 
