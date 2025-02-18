import os
import time
import numpy as np

# Chemin du PWM
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"
duty_max = 25000  # Duty cycle max en nanosecondes

# Notes et fréquences (Gamme de la mineur)
notes = {
    "La": 440.00,
    "Si": 493.88,
    "Do": 523.25,
    "Ré": 587.33,
    "Mi": 659.25,
    "Fa": 698.46,
    "Sol": 783.99
}

# Fréquence PWM (doit être beaucoup plus élevée que les fréquences des notes)
f_pwm = 40000  # 40 kHz

# Initialisation du PWM
def pwm_init(period_ns):
    if not os.path.exists(PWM_PATH):
        with open("/sys/class/pwm/pwmchip0/export", "w") as f:
            f.write("0")
    with open(PWM_PATH + "period", "w") as f:
        f.write(str(period_ns))
    with open(PWM_PATH + "enable", "w") as f:
        f.write("1")

# Met à jour le duty cycle
def update_duty_cycle(value):
    duty_ns = int(value * duty_max)
    with open(PWM_PATH + "duty_cycle", "w") as f:
        f.write(str(duty_ns))

# Générer un sinus pour une note donnée
def play_sinus(frequency, duration=1):
    samples_per_period = int(f_pwm / frequency)  # Échantillons par période
    t = np.linspace(0, 1, samples_per_period, endpoint=False)
    sin_wave = 0.5 * (1 + np.sin(2 * np.pi * t))  # Normalisé entre 0 et 1

    for _ in range(int(f_pwm * duration / samples_per_period)):
        for sample in sin_wave:
            update_duty_cycle(sample)

# Arrêter le PWM proprement
def pwm_cleanup():
    with open(PWM_PATH + "enable", "w") as f:
        f.write("0")
    with open("/sys/class/pwm/pwmchip0/unexport", "w") as f:
        f.write("0")

# Programme principal
if __name__ == "__main__":
    try:
        period_ns = int(1e9 / f_pwm)  # Fréquence PWM de 40 kHz
        pwm_init(period_ns)

        print("Lecture de la gamme de la mineur...")
        for note, freq in notes.items():
            print(f"Playing {note} ({freq} Hz)")
            play_sinus(freq, duration=1)
            time.sleep(0.1)  # Petite pause entre les notes

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
