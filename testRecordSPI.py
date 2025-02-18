#!/usr/bin/env python3
import spidev
import RPi.GPIO as GPIO
import time
import wave
import struct

# Paramètres du montage et de l'enregistrement
CS_PIN = 22              # GPIO utilisé pour la gestion manuelle du CS
SPI_BUS = 0              # SPI0
SPI_DEVICE = 0           # On ouvre /dev/spidev0.0, mais on désactive la gestion CS interne
SAMPLE_RATE = 8000       # Taux d'échantillonnage en Hz (8000 Hz pour tester)
DURATION = 10            # Durée d'enregistrement en secondes
CHANNEL_ADC = 0          # Canal du MCP3008 utilisé (0 à 7)

# Initialisation de la gestion du GPIO pour la CS manuelle
GPIO.setmode(GPIO.BCM)
GPIO.setup(CS_PIN, GPIO.OUT)
GPIO.output(CS_PIN, GPIO.HIGH)  # CS inactif

# Initialisation du périphérique SPI
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1000000  # 1 MHz (adapter si besoin)
spi.mode = 0
spi.no_cs = True          # On gère le CS manuellement via GPIO

def read_adc(channel):
    """
    Lit une valeur 10 bits du MCP3008 pour le canal donné (0-7).
    Le protocole consiste à envoyer 3 octets :
      - 1er octet : bit start (1)
      - 2ème octet : (8 + channel) << 4 (mode single-ended)
      - 3ème octet : 0 (octet de décalage)
    La réponse est sur 10 bits dans les 2 derniers octets.
    """
    cmd = [1, (8 + channel) << 4, 0]
    GPIO.output(CS_PIN, GPIO.LOW)   # Activation du CS
    resp = spi.xfer2(cmd)
    GPIO.output(CS_PIN, GPIO.HIGH)  # Désactivation du CS
    value = ((resp[1] & 3) << 8) | resp[2]
    return value

# Enregistrement des échantillons pendant DURATION secondes
print("Enregistrement en cours...")
num_samples = int(SAMPLE_RATE * DURATION)
samples = []

start_time = time.time()
for _ in range(num_samples):
    # Lecture d'un échantillon sur le canal spécifié
    adc_value = read_adc(CHANNEL_ADC)
    samples.append(adc_value)
    # Attendre le prochain échantillon (approximativement)
    time.sleep(1.0 / SAMPLE_RATE)

print("Enregistrement terminé. Nombre d'échantillons :", len(samples))

# Conversion des valeurs 10 bits (0-1023) en échantillons 16 bits signés.
# On suppose qu'une valeur médiane (environ 512) correspond au silence.
wav_samples = []
for s in samples:
    # Échelle sur 0-65535
    scaled = int((s / 1023.0) * 65535)
    # Conversion en entier signé sur 16 bits (de -32768 à 32767)
    signed = scaled - 32768
    wav_samples.append(signed)

# Enregistrement dans un fichier WAV
output_file = "audio_test.wav"
wf = wave.open(output_file, 'w')
wf.setnchannels(1)        # Mono
wf.setsampwidth(2)        # 16 bits = 2 octets par échantillon
wf.setframerate(SAMPLE_RATE)
for sample in wav_samples:
    wf.writeframes(struct.pack('<h', sample))
wf.close()

print("Fichier WAV créé :", output_file)

# Nettoyage du GPIO
GPIO.cleanup()
