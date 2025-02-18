import os
import numpy as np
import wave
from pydub import AudioSegment

PWM_PATH = "/sys/class/pwm/pwmchip0/pwm0/"


def pwm_init(period_ns):
    if not os.path.exists(PWM_PATH):
        with open("/sys/class/pwm/pwmchip0/export", "w") as f:
            f.write("0")
    with open(PWM_PATH + "duty_cycle","w")as f:
        f.write("0")
    with open(PWM_PATH + "period", "w") as f:
        f.write(str(period_ns))
    with open(PWM_PATH + "enable", "w") as f:
        f.write("1")

def update_duty_cycle(value):
    duty_ns = int(value * DUTY_MAX)
    with open(PWM_PATH + "duty_cycle", "w") as f:
        f.write(str(duty_ns))

def convert_mp3_to_wav(mp3_file, wav_file):
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format="wav")

def process_audio_file(wav_file):
    wf = wave.open(wav_file, 'rb')
    chunk = 1024
    max_amplitude = 2**15 - 1

    try:
        data = wf.readframes(chunk)
        while data:
            audio_samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            normalized_samples = (audio_samples + max_amplitude) / (2 * max_amplitude)
            for sample in normalized_samples:
                update_duty_cycle(sample)
            data = wf.readframes(chunk)
    finally:
        wf.close()

def pwm_cleanup():
    with open(PWM_PATH + "enable", "w") as f:
        f.write("0")
    with open("/sys/class/pwm/pwmchip0/unexport", "w") as f:
        f.write("0")

if __name__ == "__main__":
    try:
        pwm_frequency = 1000000
        period_ns = int(1e9 / pwm_frequency)
        pwm_init(period_ns)
        DUTY_MAX = period_ns
#        mp3_file = "/home/PFE/AudioTests/Sardines.mp3"
        wav_file = "/home/PFE/AudioTests/Podcast.wav"
#        convert_mp3_to_wav(mp3_file, wav_file)

        process_audio_file(wav_file)
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        pwm_cleanup()
