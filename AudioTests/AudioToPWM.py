import os
import numpy as np
import wave
import pyaudio
from pydub import AudioSegment

# Chemin du PWM
PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"
DUTY_MAX = 25000  # Duty cycle max en nanosecondes

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

# Mise à jour du duty cycle
def update_duty_cycle(value):
    duty_ns = int(value * DUTY_MAX)
    with open(PWM_PATH + "duty_cycle", "w") as f:
        f.write(str(duty_ns))

# Convertir un fichier MP3 en WAV
def convert_mp3_to_wav(mp3_file, wav_file):
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")

# Lecture et traitement du fichier audio
def process_audio_file(wav_file):
    # Charger le fichier WAV
    wf = wave.open(wav_file, 'rb')
    rate = wf.getframerate()
    chunk = 1024  # Taille du buffer
    max_amplitude = 2**15 - 1  # Amplitude max pour format 16 bits

    # Initialisation de PyAudio
    p = pyaudio.PyAudio()
    stream = wf.readframes

    print(f"Lecture du fichier audio {wav_file} en cours...")
    try:
        data = wf.readframes(chunk)
        while data:
            # Convertir les données audio en tableau NumPy
            audio_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            normalized_samples = (audio_samples + max_amplitude) / (2 * max_amplitude)  # Normaliser [0, 1]

            # Mettre à jour le duty cycle pour chaque échantillon
            for sample in normalized_samples:
                update_duty_cycle(sample)

            # Lire le prochain bloc
            data = wf.readframes(chunk)
    except KeyboardInterrupt:
        print("Lecture interrompue.")
    finally:
        wf.close()
        p.terminate()

# Arrêter proprement le PWM
def pwm_cleanup():
    with open(PWM_PATH + "enable", "w") as f:
        f.write("0")
    with open("/sys/class/pwm/pwmchip0/unexport", "w") as f:
        f.write("0")

# Programme principal
if __name__ == "__main__":
    try:
        # Définir la fréquence PWM
        pwm_frequency = 40000  # 40 kHz
        period_ns = int(1e9 / pwm_frequency)
        pwm_init(period_ns)

        # Convertir un fichier MP3 en WAV
        mp3_file = "/home/PFE/AudioTests/Sardines.mp3"  # Chemin vers votre fichier MP3
        wav_file = "/home/PFE/AudioTests/Sardines.wav"
        convert_mp3_to_wav(mp3_file, wav_file)

        # Lancer le traitement audio
        process_audio_file(wav_file)
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
