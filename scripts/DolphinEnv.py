#DolphinEnv.py
import sys, os, socket, struct, json, random

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))

from dolphin import event, savestate, controller
from game_memory import GameMemory
from actions import ActionSpace

HOST         = "127.0.0.1"
PORT_P1      = 55001
PORT_P2      = 55002
FRAMESKIP    = 4
STUCK_STEPS  = 225
STUCK_THRESH = 0.1

STATES_DIR = os.path.join(os.getcwd(), "save_states")

def pick_save_state():
    states = [f for f in os.listdir(STATES_DIR) if os.path.isfile(os.path.join(STATES_DIR, f))]
    if not states:
        raise RuntimeError("No save states found.")
    return os.path.join(STATES_DIR, random.choice(states))

def make_sock(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, port))
    return s

def send_json(sock, data):
    msg = json.dumps(data).encode()
    sock.sendall(struct.pack(">I", len(msg)) + msg)

def recv_action(sock):
    return struct.unpack(">I", sock.recv(4))[0]

def make_state():
    return {"done": False, "stuck_steps": 0, "last_completion": 1.0}

SAVE_STATE = pick_save_state()
mem1, mem2 = GameMemory(player_id=1), GameMemory(player_id=2)
act1, act2 = ActionSpace(use_items=False), ActionSpace(use_items=False)
sock1, sock2 = make_sock(PORT_P1), make_sock(PORT_P2)
s1, s2 = make_state(), make_state()
frame_counter = 0
initialized = False

print("[DolphinEnv] Imports OK.")
print("[DolphinEnv] Startup complete, connected to training process.")

@event.on_frameadvance
def on_frame():
    global frame_counter, initialized, s1, s2, SAVE_STATE

    if not initialized:
        savestate.load_from_file(SAVE_STATE)
        initialized = True
        print(f"[DolphinEnv] Loaded save state: {SAVE_STATE}")
        return

    frame_counter += 1
    if frame_counter % FRAMESKIP != 0:
        return

    for mem, act, sock, s, ctrl_id in [
        (mem1, act1, sock1, s1, 0),
        (mem2, act2, sock2, s2, 1),
    ]:
        if s["done"]:
            continue

        snap = mem.snapshot()
        rc   = snap["race_completion"]

        if rc >= 4.0:
            s["done"] = True
            send_json(sock, {"snapshot": snap, "done": True, "reset": False})
            print(f"[DolphinEnv] Player {ctrl_id + 1} finished.")
            continue

        if rc - s["last_completion"] < STUCK_THRESH:
            s["stuck_steps"] += 1
        else:
            s["stuck_steps"] = 0
            s["last_completion"] = rc

        send_json(sock, {"snapshot": snap, "done": False, "reset": False})
        action_idx = recv_action(sock)
        act.apply(action_idx, ctrl_id)

    p1_terminal = s1["done"] or s1["stuck_steps"] >= STUCK_STEPS
    p2_terminal = s2["done"] or s2["stuck_steps"] >= STUCK_STEPS
    if p1_terminal and p2_terminal:
        SAVE_STATE = pick_save_state()
        savestate.load_from_file(SAVE_STATE)
        send_json(sock1, {"reset": True})
        send_json(sock2, {"reset": True})
        s1, s2 = make_state(), make_state()
        frame_counter = 0
        print("[DolphinEnv] Episode reset.")