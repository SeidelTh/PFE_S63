import os
import time
import numpy as np

# Chemin du PWM
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"
duty_max = 25000  # Duty cycle max en nanosecondes

# Fréquences des notes (octaves 4 et 5)
frequencies = {
    "D5": 2*587.33,    # Ré
    "F4": 2*698.46,    # Fa
    "G4": 2*415.30,    # Solb (Sol bémol)
    "A4": 2*440.00,    # La
    "G4": 2*783.99,    # Sol
    "B4": 2*493.88,    # Si
    "C5": 2*523.25,    # Do
    "Bb4": 2*466.16,   # Si bémol
    "E5": 2*659.25     # Mi
}

# Accords II - V - I Mineur (sans quinte, avec septième)
chords = {
    "II (Dm7b5)": ["D5", "F4", "G4", "A4"],  # Dm7b5 : Ré, Fa, Solb, La
    "V (G7alt)": ["G4", "B4", "D5", "F4"],   # G7alt : Sol, Si, Ré, Fa
    "I (Cm7)": ["C5", "E5", "G4", "Bb4"]     # Cm7 : Do, Mi, Sol, Si bémol
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
def play_chord(notes, duration=2):
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

        print("Lecture de la progression II - V - I mineur...")
        for chord_name, notes in chords.items():
            print(f"Playing {chord_name}: {notes}")
            play_chord(notes, duration=.5)  # Chaque accord dure 2 secondes
            time.sleep(.2)  # Pause entre les accords

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
