#!/usr/bin/env python3
import socket
import time
import os
import threading
import json

# -------------------------------------------------------
# CONFIG BARESIP (TCP)
HOST = '127.0.0.1'
PORT = 4444

# -------------------------------------------------------
# CONFIG PWM (pour la sonnerie)
PWM0_PATH = "/sys/class/pwm/pwmchip0/pwm0"
PWM1_PATH = "/sys/class/pwm/pwmchip0/pwm1"
PERIOD_NS = 20000000  # 20 ms
DUTY_NS   = 10000000  # 10 ms

def init_pwm(pwm_path, period_ns, duty_ns):
    """Initialise le PWM si pas déjà exporté."""
    chip_path = os.path.dirname(pwm_path)
    pwm_num   = os.path.basename(pwm_path).replace("pwm", "")
    if not os.path.exists(pwm_path):
        with open(os.path.join(chip_path, "export"), "w") as f:
            f.write(pwm_num)
    with open(os.path.join(pwm_path, "period"), "w") as f:
        f.write(str(period_ns))
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write("normal")
    with open(os.path.join(pwm_path, "duty_cycle"), "w") as f:
        f.write(str(duty_ns))
    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("0")

def set_pwm(pwm_path, polarity):
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write(polarity)
    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("1")

def disable_pwm(pwm_path):
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write("normal")
    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("0")

# -------------------------------------------------------
# GESTION DE LA SONNERIE
ring_active = False

def ring_loop():
    """Boucle sonnerie tant que ring_active est True."""
    try:
        while ring_active:
            set_pwm(PWM0_PATH, "normal")
            set_pwm(PWM1_PATH, "inversed")
            print("[RINGER] Ça sonne...")
            time.sleep(1.5)
            disable_pwm(PWM0_PATH)
            disable_pwm(PWM1_PATH)
            print("[RINGER] Pause...")
            time.sleep(3)
    finally:
        disable_pwm(PWM0_PATH)
        disable_pwm(PWM1_PATH)
        print("[RINGER] Sonnerie stoppée.")

# -------------------------------------------------------
# ÉTAT DE L'APPEL
call_active = False

def auto_answer(s):
    global ring_active
    """Attend 8s après CALL_INCOMING, puis décroche si toujours en sonnerie."""
    time.sleep(4)
    if ring_active:
        print("[AUTO] Décroche automatiquement.")
        send_command(s,"/answer")
        ring_active = False

def auto_hangup(s):
    """Attend 8s après CALL_ESTABLISHED, puis raccroche si toujours en appel."""
    time.sleep(8)
    if call_active:
        print("[AUTO] Raccroche automatiquement.")
        send_command(s,"/hangup")

def send_command(s, cmd_str,params=""):

    # Construire l'objet JSON attendu
    data_obj = {
        "command": cmd_str,
        "params": params  # éventuel paramètre, ex: "sip:[email protected]"
        # "token": "some_id" # optionnel si tu veux un token
    }

    # Encoder en JSON
    json_str = json.dumps(data_obj)  # ex: '{"command":"answer","params":""}'

    # L'encapsuler en netstring : "<len>:<json>,"
    netstring = f"{len(json_str)}:{json_str},"

    # Envoyer au plugin ctrl_tcp
    s.sendall(netstring.encode())

# -------------------------------------------------------
# INITIALISATION PWM
init_pwm(PWM0_PATH, PERIOD_NS, DUTY_NS)
init_pwm(PWM1_PATH, PERIOD_NS, DUTY_NS)

def main():
    global ring_active, call_active

    print("[MAIN] Connexion à Baresip (TCP).")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"[MAIN] Connecté sur {HOST}:{PORT}.")

        while True:
            data = s.recv(1024)
            if not data:
                break
            message = data.decode(errors='replace')

            # Appel entrant
            if "CALL_INCOMING" in message:
                print("[EVENT] Appel entrant !")
                ring_active = True
                call_active = False
                # Lance la sonnerie
                threading.Thread(target=ring_loop, daemon=True).start()
                # Lance auto_answer dans 8s
                threading.Thread(target=auto_answer, args=(s,), daemon=True).start()

            # Appel établi
            if "CALL_ESTABLISHED" in message or "200" in message:
                print("[EVENT] Appel décroché (établi).")
                # Stoppe la sonnerie
                ring_active = False
                # Active le flag d'appel
                call_active = True
                # Lance auto_hangup dans 8s
                threading.Thread(target=auto_hangup, args=(s,), daemon=True).start()

            # Fin d’appel
            if "CALL_CLOSED" in message or "CALL_TERMINATED" in message:
                print("[EVENT] Fin d’appel.")
                ring_active = False
                call_active = False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[MAIN] Interruption clavier.")
    finally:
        ring_active = False
        call_active = False
        time.sleep(1)
        disable_pwm(PWM0_PATH)
        disable_pwm(PWM1_PATH)
        print("[MAIN] Script terminé.")
