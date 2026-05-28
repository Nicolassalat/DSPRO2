#StartTraining.py
import os, sys, time, re, subprocess, json, threading
import tkinter as tk

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR   = os.path.join(PROJECT_ROOT, "scripts")
ISO_PATH      = os.path.join(PROJECT_ROOT, "game", "mkw.iso")
DOLPHIN_EXE   = os.path.join(PROJECT_ROOT, "emulator", "Dolphin.exe")
ENV_SCRIPT    = os.path.join(SCRIPTS_DIR, "dolphin_env.py")
READY_FILE    = os.path.join(PROJECT_ROOT, "training_ready.txt")
DOLPHIN_INI   = os.path.join(os.environ["APPDATA"], "Dolphin Emulator", "Config", "Dolphin.ini")
STATE_FILE    = os.path.join(SCRIPTS_DIR, "training_state.json")
CRASH_LOG = os.path.join(PROJECT_ROOT, "crash_log.txt")
EMULATION_SPEED = 1.0

stop_requested = False
crash_count = 0

def get_episode_count():
    try:
        with open(STATE_FILE) as f:
            return json.load(f).get("episode_count", 0)
    except Exception:
        return 0

def log_crash(message):
    episode = get_episode_count()
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] episode={episode} {message}\n"
    with open(CRASH_LOG, "a") as f:
        f.write(entry)

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

def launch_stop_gui():
    def on_stop():
        global stop_requested
        stop_requested = True
        btn.config(text="Stopping...", state="disabled")
        label.config(text="Waiting for current episode to finish...")

    root = tk.Tk()
    root.title("Training Control")
    root.geometry("300x120")
    root.resizable(False, False)

    global label
    label = tk.Label(root, text=f"Training running. Crashes: {crash_count}", font=("Arial", 10))
    label.pack(pady=10)

    btn = tk.Button(root, text="Stop Training", command=on_stop,
                    bg="red", fg="white", font=("Arial", 12), width=20)
    btn.pack(pady=5)

    def update_label():
        label.config(text=f"Training running. Crashes: {crash_count}")
        root.after(2000, update_label)

    root.after(2000, update_label)
    root.mainloop()

threading.Thread(target=launch_stop_gui, daemon=True).start()

set_emulation_speed(EMULATION_SPEED)

run_number = 0

while True:
    run_number += 1
    print(f"[StartTraining] Starting run #{run_number} (crashes so far: {crash_count})")

    if os.path.exists(READY_FILE):
        os.remove(READY_FILE)

    print("[StartTraining] Launching TrainingProcess...")
    training_proc = subprocess.Popen(
        [sys.executable, os.path.join(SCRIPTS_DIR, "training_process.py")],
    )

    print("[StartTraining] Waiting for TrainingProcess to be ready...")
    while not os.path.exists(READY_FILE):
        time.sleep(0.1)

    print("[StartTraining] TrainingProcess ready.")

    print("[StartTraining] Launching Dolphin...")
    try:
        dolphin_proc = subprocess.Popen(
            [DOLPHIN_EXE,
            "-e", ISO_PATH,
            "--script", ENV_SCRIPT],
        )
    except Exception as e:
        print(f"[StartTraining] Failed to launch Dolphin: {e}")
        break

    print("[StartTraining] All systems go.")

    # Wait for either stop request or training process exit
    while training_proc.poll() is None:
        if stop_requested:
            print("[StartTraining] Stop requested. Shutting down...")
            training_proc.terminate()
            dolphin_proc.kill()
            training_proc.wait()
            dolphin_proc.wait()
            print(f"[StartTraining] Training stopped cleanly after {run_number} episodes, with {crash_count} crashes.")
            sys.exit(0)
        time.sleep(1)

    # TrainingProcess exited on its own
    if stop_requested:
        dolphin_proc.kill()
        dolphin_proc.wait()
        log_crash("Clean stop")
        sys.exit(0)
    elif dolphin_proc.poll() is not None:
        # Dolphin also exited — it crashed
        crash_count += 1
        log_crash(f"Dolphin crash #{crash_count}")
        time.sleep(5)
        print("[StartTraining] Restarting...")
    else:
        # Dolphin still running but TrainingProcess died unexpectedly
        crash_count += 1
        log_crash(f"TrainingProcess crash #{crash_count}")
        dolphin_proc.kill()
        dolphin_proc.wait()
        time.sleep(5)
        print("[StartTraining] Restarting...")