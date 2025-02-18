import time
import os

# Chemins des PWM
PWM0_PATH = "/sys/class/pwm/pwmchip0/pwm0"
PWM1_PATH = "/sys/class/pwm/pwmchip0/pwm1"

# Fonction pour initialiser un PWM
def init_pwm(pwm_path, period_ns, duty_ns):
    # Exporter le PWM si nécessaire, c-à-d créer le dossier
    if not os.path.exists(pwm_path):
        chip_path = os.path.dirname(pwm_path)
        with open(os.path.join(chip_path, "export"), "w") as f:
            f.write(pwm_path.split("pwm")[-1])  # Exporte pwmX (ex: "0" ou "1")

    # Configurer la période - doit être fait avant le duty cycle pour éviter 
    # les conflits de duty cylce > période
    with open(os.path.join(pwm_path, "period"), "w") as f:
        f.write(str(period_ns))

    # Configurer la polarité (normal), uniquement pour le setup
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write("normal")

    # Configurer le duty cycle
    with open(os.path.join(pwm_path, "duty_cycle"), "w") as f:
        f.write(str(duty_ns))

    # Désactiver pour éviter des erreurs lors de modifications
    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("0")

# Fonction pour activer un PWM avec une polarité
def set_pwm(pwm_path, polarity):
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write(str(polarity))

    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("1")

# Fonction pour désactiver un PWM
def disable_pwm(pwm_path):
    # On force les deux pwm à une polarité normale, car un pwm désactivé 
    # inversé est toujours à 1.
    with open(os.path.join(pwm_path, "polarity"), "w") as f:
        f.write("normal")
    with open(os.path.join(pwm_path, "enable"), "w") as f:
        f.write("0")

# Configuration des PWM
PERIOD_NS = 20000000  # 20 ms (50 Hz)
DUTY_NS = 10000000    # 10 ms

init_pwm(PWM0_PATH, PERIOD_NS, DUTY_NS)
init_pwm(PWM1_PATH, PERIOD_NS, DUTY_NS)

# Boucle principale pour cadencer les PWM
try:
    while True:
        # Activer PWM0 et PWM1 avec des polarités inversées (sonnerie de 1.5 s)
        set_pwm(PWM0_PATH, "normal")
        set_pwm(PWM1_PATH, "inversed")
        print("ça sonne...")
        time.sleep(1.5)

        # Pause de 3 secondes (les PWM sont désactivés)
        disable_pwm(PWM0_PATH)
        disable_pwm(PWM1_PATH)
        print("et ça attend.")
        time.sleep(3)

except KeyboardInterrupt:
    # Arrêter proprement en cas d'interruption
    print("Arrêt du script...")

finally:
    # Désactiver les PWM avant de quitter
    disable_pwm(PWM0_PATH)
    disable_pwm(PWM1_PATH)
    print("pwms coupées!")
