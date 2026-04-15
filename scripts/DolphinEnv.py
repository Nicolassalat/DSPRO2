#DolphinEnv.py
import sys, os, socket, struct, json, random

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))

from dolphin import event, savestate
#from dolphin import gui
from game_memory import GameMemory
from actions import ActionSpace

HOST         = "127.0.0.1"
PORT_P1      = 55001
PORT_P2      = 55002
FRAMESKIP    = 4
STUCK_STEPS  = 225
STUCK_THRESH = 0.01

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
    return {"done": False, "stuck": False, "stuck_steps": 0, "last_completion": 1.0}

def _draw_overlay(snap1, snap2, s1, s2):
    mx, my = 10.0, 10.0
    lh, pad, bw = 20.0, 8.0, 500.0
    bh = 6 * lh + 2 * pad

    gui.draw_rect_filled((mx, my), (mx + bw, my + bh), 0xCC111111)
    gui.draw_rect((mx, my), (mx + bw, my + bh), 0x88FFFFFF)

    tx, ty = mx + pad, my + pad
    for label, snap, s in [("P1", snap1, s1), ("P2", snap2, s2)]:
        rc = snap["race_completion"]
        pct = (rc - 1.0) / 3.0 * 100.0
        gui.draw_text((tx, ty), 0xFF00E5FF, f"{label}  progress: {rc:.2f} ({pct:.1f}%)  stuck: {s['stuck_steps']}/{STUCK_STEPS}")
        ty += lh
        gui.draw_text((tx, ty), 0xFFFFFFFF, f"    speed: {snap['speed']:.1f}  offroad: {snap['is_offroad']}  done: {s['done']}  stuck: {s['stuck']}")
        ty += lh

SAVE_STATE = pick_save_state()
mem1, mem2 = GameMemory(player_id=0), GameMemory(player_id=1)
act1, act2 = ActionSpace(use_items=False), ActionSpace(use_items=False)
sock1, sock2 = make_sock(PORT_P1), make_sock(PORT_P2)
s1, s2 = make_state(), make_state()
frame_counter = 0
initialized = False

print("[DolphinEnv] Imports OK.")
print("[DolphinEnv] Startup complete, connected to training process.")
# _last_snap1, _last_snap2 = None, None

@event.on_frameadvance
def on_frame():
    global frame_counter, initialized, s1, s2, SAVE_STATE, _last_snap1, _last_snap2

    if not initialized:
        savestate.load_from_file(SAVE_STATE)
        initialized = True
        print(f"[DolphinEnv] Loaded save state: {SAVE_STATE}")
        return

    # For debugging: draw an overlay with progress and status info
    #if _last_snap1 and _last_snap2:
    #    _draw_overlay(_last_snap1, _last_snap2, s1, s2)

    frame_counter += 1
    if frame_counter % FRAMESKIP != 0:
        return
    
    for mem, act, sock, s, ctrl_id in [
        (mem1, act1, sock1, s1, 0),
        (mem2, act2, sock2, s2, 1),
    ]:
        snap = mem.snapshot()
        if ctrl_id == 0:
            _last_snap1 = snap
        else:
            _last_snap2 = snap

        if s["done"]:
            continue

        rc = snap["race_completion"]

        if rc >= 4.0:
            s["done"] = True
            send_json(sock, {"snapshot": snap, "done": True, "reset": False})
            print(f"[DolphinEnv] Player {ctrl_id + 1} finished.")
            continue

        if rc - s["last_completion"] < STUCK_THRESH:
            s["stuck_steps"] += 1
            if s["stuck_steps"] >= STUCK_STEPS:
                s["stuck"] = True
        else:
            s["stuck_steps"] = 0
            s["last_completion"] = rc
            s["stuck"] = False

        send_json(sock, {"snapshot": snap, "done": False, "reset": False})
        action_idx = recv_action(sock)
        if ctrl_id != 0:
            act.apply(action_idx, ctrl_id)

    p1_terminal = s1["done"] or s1["stuck"]
    p2_terminal = s2["done"] or s2["stuck"]

    if p1_terminal and p2_terminal:
        SAVE_STATE = pick_save_state()
        savestate.load_from_file(SAVE_STATE)
        send_json(sock1, {"reset": True})
        send_json(sock2, {"reset": True})
        s1, s2 = make_state(), make_state()
        frame_counter = 0
        print("[DolphinEnv] Episode reset.")