# start_eval.py
import os, sys, time, subprocess, argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR  = os.path.join(PROJECT_ROOT, "scripts")
ISO_PATH     = os.path.join(PROJECT_ROOT, "game", "mkw.iso")
DOLPHIN_EXE  = os.path.join(PROJECT_ROOT, "emulator", "Dolphin.exe")
ENV_SCRIPT   = os.path.join(SCRIPTS_DIR, "env", "dolphin_env.py")
READY_FILE   = os.path.join(PROJECT_ROOT, "training_ready.txt")

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, help="Path to agent_model.pth to evaluate")
parser.add_argument("--episodes", type=int, default=20)
args = parser.parse_args()

if os.path.exists(READY_FILE):
    os.remove(READY_FILE)

print(f"[StartEval] Model: {args.model}")
print("[StartEval] Launching evaluate.py...")
eval_proc = subprocess.Popen(
    [sys.executable, os.path.join(SCRIPTS_DIR, "eval", "evaluate.py"),
     "--model", args.model,
     "--episodes", str(args.episodes)],
)

while not os.path.exists(READY_FILE):
    time.sleep(0.1)
print("[StartEval] evaluate.py ready.")

print("[StartEval] Launching Dolphin...")
try:
    dolphin_proc = subprocess.Popen(
        [DOLPHIN_EXE, "-e", ISO_PATH, "--script", ENV_SCRIPT],
    )
except Exception as e:
    print(f"[StartEval] Failed to launch Dolphin: {e}")
    eval_proc.terminate()
    sys.exit(1)

print("[StartEval] Running evaluation...")
eval_proc.wait()
dolphin_proc.kill()
dolphin_proc.wait()
print("[StartEval] Done.")
