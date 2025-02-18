import os
import time
import numpy as np

# Chemin du PWM (à adapter selon le système)
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"

# Paramètres
f_sinus = 440          # Fréquence du signal sinus (Hz)
f_pwm = 40000          # Fréquence PWM (Hz)
amplitude = 0.5        # Amplitude relative du signal (entre 0 et 1)
duty_max = 25000     # Valeur max de duty_cycle en nanosecondes = period
period_ns = int(1e9 / f_pwm)  # Période PWM en nanosecondes

# Générer les points du sinus
samples_per_period = int(f_pwm / f_sinus)  # Nombre d'échantillons par période du sinus
t = np.linspace(0, 1, samples_per_period, endpoint=False)
sin_wave = 0.5 * (1 + amplitude * np.sin(2 * np.pi * t))  # Normalisé entre 0 et 1

# Initialisation du PWM
def pwm_init():
    # Activer le canal PWM
    if not os.path.exists(PWM_PATH):
        with open("/sys/class/pwm/pwmchip0/export", "w") as f:
            f.write("0")
    with open(PWM_PATH + "duty_cycle","w") as f:
            f.write("0")
    try:
        print("Trying to set period_ns to:", period_ns)
        with open(PWM_PATH + "period", "w") as f:
            f.write(str(period_ns))
    except OSError as e:
        print(f"Error setting period: {e}")
        print("Check if the frequency is supported by your hardware.")
        raise
    # Activer le PWM
    with open(PWM_PATH + "enable", "w") as f:
        f.write("1")

# Met à jour le duty_cycle
def update_duty_cycle(value):
    duty_ns = int(value * duty_max)
    with open(PWM_PATH + "duty_cycle", "w") as f:
        f.write(str(duty_ns))

# Arrêter le PWM proprement
def pwm_cleanup():
    with open(PWM_PATH + "enable", "w") as f:
        f.write("0")
    with open("/sys/class/pwm/pwmchip0/unexport", "w") as f:
        f.write("0")

# Programme principal
try:
    pwm_init()
    print("PWM en cours de génération. Appuyez sur Ctrl+C pour arrêter.")
    while True:
        for duty in sin_wave:
            update_duty_cycle(duty)
            time.sleep(1 / f_pwm)  # Attente avant de passer au prochain échantillon
except KeyboardInterrupt:
    print("Arrêt du PWM.")
finally:
    pwm_cleanup()
