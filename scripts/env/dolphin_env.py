#DolphinEnv.py
import sys, os, socket, struct, json, random, select

sys.path.insert(0, os.path.join(os.getcwd(), "env"))
sys.path.insert(0, os.getcwd())

from dolphin import event, savestate
from dolphin import gui
from game_memory import GameMemory
from actions import ActionSpace

HOST         = "127.0.0.1"
PORT_P1      = 55001
PORT_P2      = 55002
FRAMESKIP    = 4
STUCK_STEPS  = 225
STUCK_THRESH = 0.01
WINDOW_SIZE = 30
REQUIRED_FINISH_RATE = 0.65
COMPLETIONS_TO_UNLOCK = 75


STATES_BASE = os.path.join(os.getcwd(), "..", "save_states") if os.path.basename(os.getcwd()).lower() == "scripts" else os.path.join(os.getcwd(), "save_states")
STATE_FILE = os.path.join(os.getcwd(), "training_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                return (data.get("episode_count", 0),
                        data.get("track_completions", {"lc": 0, "mc": 0, "mrw": 0, "dc": 0}),
                        data.get("track_recent", {"lc": [], "mc": [], "mrw": [], "dc": []}))
        except Exception:
            pass
    return 0, {"lc": 0, "mc": 0, "mrw": 0, "dc": 0}, {"lc": [], "mc": [], "mrw": [], "dc": []}

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({"episode_count": episode_count, "track_completions": track_completions, "track_recent": track_recent}, f)

episode_count, track_completions, track_recent = load_state()

TRACK_FOLDERS = {
    "lc":  os.path.join(STATES_BASE, "lc"),
    "mc":  os.path.join(STATES_BASE, "mc"),
    "mrw": os.path.join(STATES_BASE, "mrw"),
    "dc":  os.path.join(STATES_BASE, "dc"),
}

def get_active_tracks():
    if track_completions["lc"] < COMPLETIONS_TO_UNLOCK:
        return ["lc"]
    elif track_completions["mc"] < COMPLETIONS_TO_UNLOCK:
        return ["lc", "mc"]
    elif track_completions["mrw"] < COMPLETIONS_TO_UNLOCK:
        return ["lc", "mc", "mrw"]
    else:
        return ["lc", "mc", "mrw", "dc"]

def get_newest_track():
    active = get_active_tracks()
    return active[-1]

def pick_save_state():
    active = get_active_tracks()
    track = random.choice(active)
    folder = TRACK_FOLDERS[track]
    states = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not states:
        raise RuntimeError(f"No save states found in {folder}")
    return os.path.join(folder, random.choice(states))

def make_sock(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, port))
    return s

def send_json(sock, data):
    msg = json.dumps(data).encode()
    sock.sendall(struct.pack(">I", len(msg)) + msg)

def recv_action(sock):
    return struct.unpack(">I", sock.recv(4))[0]

def try_recv_action(sock):
    """Drain all pending actions, return the latest one or None if nothing ready."""
    action = None
    while True:
        ready, _, _ = select.select([sock], [], [], 0)
        if not ready:
            break
        data = sock.recv(4)
        if len(data) < 4:
            break
        action = struct.unpack(">I", data)[0]
    return action

def make_state():
    return {"done": False, "stuck": False, "stuck_steps": 0, "last_completion": 1.0}

"""
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
"""

last_actions = {0: 0, 1: 0}

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
    global frame_counter, initialized, s1, s2, SAVE_STATE, last_actions

    if not initialized:
        savestate.load_from_file(SAVE_STATE)
        initialized = True
        print(f"[DolphinEnv] Loaded save state: {SAVE_STATE}")
        return

    # For debugging: draw an overlay with progress and status info
    #if _last_snap1 and _last_snap2:
    #    _draw_overlay(_last_snap1, _last_snap2, s1, s2)

    for act, ctrl_id in [(act1, 0), (act2, 1)]:
        act.apply(last_actions[ctrl_id], ctrl_id)

    frame_counter += 1
    if frame_counter % FRAMESKIP != 0:
        return

    for mem, act, sock, s, ctrl_id in [
        (mem1, act1, sock1, s1, 0),
        (mem2, act2, sock2, s2, 1),
    ]:
        snap = mem.snapshot()

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
        new_action = try_recv_action(sock)
        if new_action is not None:
            last_actions[ctrl_id] = new_action
        gui.draw_text((10, 30 + ctrl_id * 20), 0xFFFFFFFF, f"P{ctrl_id + 1}: {act.get_action_name(last_actions[ctrl_id])}")

    p1_terminal = s1["done"] or s1["stuck"]
    p2_terminal = s2["done"] or s2["stuck"]

    if p1_terminal and p2_terminal:
        global episode_count, track_completions, track_recent
        episode_count += 1
        current_track = os.path.basename(os.path.dirname(SAVE_STATE))
        new_track_unlocked = False

        if current_track == get_newest_track():
            finished = 1 if (s1["done"] or s2["done"]) else 0
            track_recent[current_track].append(finished)
            if len(track_recent[current_track]) > WINDOW_SIZE:
                track_recent[current_track].pop(0)
            recent = track_recent[current_track]
            if len(recent) == WINDOW_SIZE:
                finish_rate = sum(recent) / WINDOW_SIZE
                if finish_rate >= REQUIRED_FINISH_RATE:
                    track_completions[current_track] = COMPLETIONS_TO_UNLOCK
                    new_track_unlocked = True
                    print(f"[DolphinEnv] {current_track} mastered! Unlocking next track. finish_rate={finish_rate:.1%}")

        save_state()
        print(f"[DEBUG] DolphinEnv episode count incremented: {episode_count}")
        SAVE_STATE = pick_save_state()
        savestate.load_from_file(SAVE_STATE)
        send_json(sock1, {"reset": True, "stuck": s1["stuck"], "track": current_track, "snapshot": new_track_unlocked})
        send_json(sock2, {"reset": True, "stuck": s2["stuck"], "track": current_track, "snapshot": new_track_unlocked})
        s1, s2 = make_state(), make_state()
        frame_counter = 0
        print(f"[DolphinEnv] Episode reset. episode={episode_count} tracks={get_active_tracks()}")