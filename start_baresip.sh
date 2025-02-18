#!/usr/bin/env bash

# Lancer Baresip (en arrière‐plan)
baresip &

# Attendre 2s pour que Baresip initialise le port TCP
sleep 2

# Lancer le script de contrôle
python3 /home/PFE/baresip_ctrl.py
