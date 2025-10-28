import os
import subprocess

# Chemin du fichier contenant les informations WiFi
wifi_config_file = "/home/projet_musee/wifi_logs.txt"

def read_wifi_credentials(file_path):
    """
    Lit le fichier de configuration WiFi et retourne le SSID, le mot de passe et le nom de la Raspberry Pi.
    """
    ssid, password, name = None, None, None
    try:
        with open(file_path, "r") as file:
            for line in file:
                if line.startswith("SSID="):
                    ssid = line.strip().split("=")[1]
                elif line.startswith("PASSWORD="):
                    password = line.strip().split("=")[1]
                elif line.startswith("NAME="):
                    name = line.strip().split("=")[1]
        if not ssid or not password or not name:
            raise ValueError("SSID, mot de passe ou nom manquant dans le fichier.")
        return ssid, password, name
    except Exception as e:
        print(f"Erreur lors de la lecture des informations WiFi : {e}")
        return None, None, None

def configure_wifi(ssid, password):
    """
    Configure le fichier wpa_supplicant.conf avec les informations WiFi fournies.
    """
    try:
        wpa_supplicant_config = f"""
        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1
        country=FR

        network={{
            ssid="{ssid}"
            psk="{password}"
        }}
        """
        # Écrire dans le fichier wpa_supplicant.conf
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as file:
            file.write(wpa_supplicant_config.strip())
        print(f"WiFi configuré avec SSID: {ssid}")
    except Exception as e:
        print(f"Erreur lors de la configuration du WiFi : {e}")

def set_hostname(name):
    """
    Configure le nom d’hôte (hostname) de la Raspberry Pi et met à jour les fichiers nécessaires.
    """
    try:
        # Mettre à jour le fichier /etc/hostname
        with open("/etc/hostname", "w") as hostname_file:
            hostname_file.write(name + "\n")

        # Mettre à jour le fichier /etc/hosts
        with open("/etc/hosts", "r") as hosts_file:
            hosts_content = hosts_file.readlines()
        with open("/etc/hosts", "w") as hosts_file:
            for line in hosts_content:
                if "127.0.1.1" in line:
                    hosts_file.write(f"127.0.1.1       {name}\n")
                else:
                    hosts_file.write(line)

        # Appliquer le nom d'hôte immédiatement
        subprocess.run(["sudo", "hostnamectl", "set-hostname", name])
        print(f"Nom d’hôte configuré : {name}")

    except Exception as e:
        print(f"Erreur lors de la configuration du nom d’hôte : {e}")

def restart_network_services():
    """
    Redémarre les services réseau pour appliquer les changements.
    """
    try:
        # Redémarrer le service réseau
        os.system("sudo systemctl restart networking")
        print("Service réseau redémarré.")

        # Redémarrer Avahi pour mDNS
        os.system("sudo systemctl restart avahi-daemon")
        print("Service Avahi redémarré pour mDNS.")

    except Exception as e:
        print(f"Erreur lors du redémarrage des services réseau : {e}")

if __name__ == "__main__":
    # Lire les informations WiFi et le nom
    ssid, password, name = read_wifi_credentials(wifi_config_file)
    if ssid and password and name:
        # Configurer le WiFi
        configure_wifi(ssid, password)
        # Configurer le nom de la Raspberry Pi
        set_hostname(name)
        # Redémarrer les services réseau
        restart_network_services()
    else:
        print("Impossible de configurer le WiFi en raison de données manquantes.")
