import os
import time
import numpy as np

# Chemin du PWM
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"
duty_max = 25000  # Duty cycle max en nanosecondes

# Fréquences des notes
frequencies = {
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "F4": 698.46,
    "G4": 783.99,
    "G#4": 830.61
}

# Accords de II - V - i en La mineur
chords = {
    "II (Dm)": ["D5", "F4", "A4"],
    "V (G)": ["G4", "B4", "D5"],
    "i (Am)": ["A4", "C5", "E5"]
}

# Fréquence PWM
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

# Jouer un accord
def play_chord(notes, duration=1):
    # Générer un signal combiné pour les notes
    t = np.linspace(0, duration, int(f_pwm * duration), endpoint=False)
    combined_wave = np.zeros_like(t)

    for note in notes:
        freq = frequencies[note]
        combined_wave += np.sin(2 * np.pi * freq * t)
    
    # Normalisation pour éviter les saturations
    combined_wave = 0.5 * (1 + combined_wave / np.max(np.abs(combined_wave)))

    # Appliquer le signal au PWM
    for sample in combined_wave:
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

        print("Lecture de la progression II - V - i en La mineur...")
        for chord_name, notes in chords.items():
            print(f"Playing {chord_name}: {notes}")
            play_chord(notes, duration=0.3)  # Chaque accord dure 2 secondes
            time.sleep(0.5)  # Pause entre les accords

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
