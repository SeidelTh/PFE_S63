import os
import time
import numpy as np

# Chemin du PWM
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"
duty_max = 25000  # Duty cycle max en nanosecondes

# Fréquences des notes (octave 4 et 5)
frequencies = {
    "C4": 2*261.63,    # Do (octave 4)
    "D4": 2*293.66,    # Ré
    "E4": 2*329.63,    # Mi
    "F4": 2*349.23,    # Fa
    "G4": 2*392.00,    # Sol
    "A4": 2*440.00,    # La
    "B4": 2*493.88,    # Si
    "C5": 2*523.25,    # Do (octave 5)
    "G3": 2*196.00,    # Sol (grave)
    "x" : 1
}

# Notes de la mélodie de "Frère Jacques"
melody = [
    ["C4", "D4", "E4", "C4", "C4","D4","E4","C4"],    # Frère Jacques
    ["E4", "F4", "G4","x","E4","F4","G4","x"],          # Dormez-vous ?
    ["G4", "A4", "E4", "C4","G4","A4","E4","C4"],  # Sonnez les matines
    ["C4", "G3", "C4","x","C4","G3","C4","x"]           # Ding, dang, dong
]

# Durée des notes (en secondes)
note_duration = 0.2  # Durée de chaque note
pause_duration = 0.05  # Pause entre les notes

# Fréquence PWM
f_pwm = 40000  # 40 kHz

# Initialisation du PWM
def pwm_init(period_ns):
    if not os.path.exists(PWM_PATH):
        with open("/sys/class/pwm/pwmchip0/export", "w") as f:
            f.write("0")
    with open(PWM_PATH + "duty_cycle","w") as f:
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

# Jouer une note
def play_note(note, duration=0.5):
    freq = frequencies[note]
    t = np.linspace(0, duration, int(f_pwm * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    wave = 0.5 * (1 + wave / np.max(np.abs(wave)))  # Normalisation

    # Appliquer le signal au PWM
    for sample in wave:
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

        print("Lecture de la mélodie de Frère Jacques...")
        for phrase in melody:
            for note in phrase:
                play_note(note, note_duration)
                time.sleep(pause_duration)

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
