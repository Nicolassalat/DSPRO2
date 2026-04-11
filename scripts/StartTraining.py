#StartTraining.py
import os, sys, time, re, subprocess

PROJECT_ROOT  = r"C:\Users\Nicolas\LocalDocuments\HSLU\DSPRO2"
SCRIPTS_DIR   = os.path.join(PROJECT_ROOT, "scripts")
ISO_PATH      = os.path.join(PROJECT_ROOT, "game", "mkw.iso")
DOLPHIN_EXE   = os.path.join(PROJECT_ROOT, "emulator", "Dolphin.exe")
ENV_SCRIPT    = os.path.join(SCRIPTS_DIR, "DolphinEnv.py")
READY_FILE    = os.path.join(PROJECT_ROOT, "training_ready.txt")
DOLPHIN_INI   = os.path.join(os.environ["APPDATA"], "Dolphin Emulator", "Config", "Dolphin.ini")
EMULATION_SPEED = 2.0

def set_emulation_speed(speed):
    with open(DOLPHIN_INI, "r") as f:
        config = f.read()
    if re.search(r"EmulationSpeed\s*=\s*[\d.]+", config):
        config = re.sub(r"EmulationSpeed\s*=\s*[\d.]+", f"EmulationSpeed = {speed}", config)
    elif "[Core]" in config:
        config = config.replace("[Core]", f"[Core]\nEmulationSpeed = {speed}")
    else:
        config += f"\n[Core]\nEmulationSpeed = {speed}\n"
    with open(DOLPHIN_INI, "w") as f:
        f.write(config)
    print(f"[StartTraining] Emulation speed set to {int(speed * 100)}%.")

if os.path.exists(READY_FILE):
    os.remove(READY_FILE)

set_emulation_speed(EMULATION_SPEED)

print("[StartTraining] Launching TrainingProcess...")
training_proc = subprocess.Popen(
    [sys.executable, os.path.join(SCRIPTS_DIR, "TrainingProcess.py")],
)

print("[StartTraining] Waiting for TrainingProcess to be ready...")
while not os.path.exists(READY_FILE):
    time.sleep(0.1)
print("[StartTraining] TrainingProcess ready.")

print("[StartTraining] Launching Dolphin...")
subprocess.Popen([
    DOLPHIN_EXE,
    "-e", ISO_PATH,
    "--script", ENV_SCRIPT,f
])

print("[StartTraining] All systems go.")
training_proc.wait()