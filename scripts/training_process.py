# TrainingProcess.py
from collections import deque
import numpy as np
import socket, struct, json, threading, os, time, random

from dolphin_capture import DolphinCapture
from reward_function import simple_reward, advanced_reward
from neural_agent import NeuralAgent

HOST       = "127.0.0.1"
PORT_P1    = 55001
PORT_P2    = 55002
READY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "training_ready.txt")
ACTION_NAMES = [
    "accel_center", "accel_left", "accel_right",
    "drift_hard_left", "drift_soft_left", "drift_center", "drift_soft_right", "drift_hard_right",
    "wheelie_center", "wheelie_left", "wheelie_right",
    "brake_center", "brake_left", "brake_right",
    "nothing"
]

USE_ADVANCED_REWARD = True


agent = NeuralAgent(num_actions=15)
FRAME_STACK = 4
frame_buffers = {1: deque(maxlen=FRAME_STACK), 2: deque(maxlen=FRAME_STACK)}
compute_reward = advanced_reward if USE_ADVANCED_REWARD else simple_reward

def get_stacked_frame(player_id, new_frame):
    if new_frame is None:
        return None
    buf = frame_buffers[player_id]
    buf.append(np.array(new_frame, dtype=np.float32))
    while len(buf) < FRAME_STACK:
        buf.append(np.array(new_frame, dtype=np.float32))
    return np.stack(list(buf), axis=0)  # → [4, H, W]

def load_episode_offset():
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_state.json")
    try:
        with open(state_file) as f:
            return json.load(f).get("episode_count", 0)
    except Exception:
        return 0

def send_action(sock, action_idx):
    sock.sendall(struct.pack(">I", action_idx))

def recv_json(sock):
    raw_len = sock.recv(4)
    if not raw_len:
        return None
    length = struct.unpack(">I", raw_len)[0]
    data = b""
    while len(data) < length:
        data += sock.recv(length - len(data))
    return json.loads(data.decode())

def make_capture(player_id, retries=20, delay=1.0):
    for i in range(retries):
        try:
            return DolphinCapture(player_id=player_id)
        except RuntimeError:
            print(f"[TrainingProcess] Dolphin window not ready, retry {i+1}/{retries}...")
            time.sleep(delay)
    raise RuntimeError("Dolphin window never appeared.")

def player_loop(player_id, conn):
    cap = make_capture(player_id)
    last_rc = 1.0
    episode_reward = 0.0
    episode_steps = 0
    start_rc = None
    episode_num = load_episode_offset() + 1
    action_counts = [0] * 15

    while True:
        try:
            msg = recv_json(conn)
        except ConnectionResetError:
            break

        if msg is None:
            print(f"[TrainingProcess] Player {player_id} disconnected.")
            break

        if msg.get("reset"):
            stuck = msg.get("stuck", False)
            track = msg.get("track", "unknown")
            snapshot = msg.get("snapshot", False)
            r = compute_reward({}, progress_delta=0.0, done=not stuck, stuck=stuck)
            episode_reward += r
            frame_buffers[player_id].clear()
            frame = cap()
            stacked = get_stacked_frame(player_id, frame)
            if stacked is not None:
                agent.step(player_id, stacked, r, terminal=True)
            print(
                f"[TrainingProcess] P{player_id} episode {episode_num} end. stuck={stuck} total_reward={episode_reward:.2f}")
            agent.writer.add_scalar(f"episode/P{player_id}_reward", episode_reward, episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_length", episode_steps, episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_stuck", int(stuck), episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_progress", last_rc - (start_rc or 1.0), episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_reward_per_step", episode_reward / max(episode_steps, 1), episode_num)
            agent.writer.add_scalars("episode/reward", {f"P{player_id}": episode_reward}, episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_reward_{track}", episode_reward, episode_num)
            agent.writer.add_scalars(f"episode/reward_{track}", {f"P{player_id}": episode_reward}, episode_num)
            for i, count in enumerate(action_counts):
                agent.writer.add_scalar(f"actions/P{player_id}_{ACTION_NAMES[i]}", count, episode_num)

            # Snapshot on track unlock — only P1 triggers to avoid double-save
            if snapshot and player_id == 1:
                print(f"[TrainingProcess] New track unlocked after {track} — saving snapshot...")
                agent.save_snapshot(track)

            action_counts = [0] * 15
            episode_num += 1
            last_rc = 1.0
            episode_reward = 0.0
            episode_steps = 0
            start_rc = None
            continue

        if msg.get("done"):
            snap = msg.get("snapshot", {})
            r = compute_reward(snap, progress_delta=0.0, done=True, stuck=False)
            episode_reward += r
            frame = cap()
            stacked = get_stacked_frame(player_id, frame)
            if stacked is not None:
                agent.step(player_id, stacked, r, terminal=True)
            continue

        snap = msg["snapshot"]
        frame = cap()
        rc = snap["race_completion"]
        if start_rc is None:
            start_rc = rc
        progress_delta = rc - last_rc
        last_rc = rc
        r = compute_reward(snap, progress_delta, done=False, stuck=False)
        episode_reward += r
        episode_steps += 1
        stacked = get_stacked_frame(player_id, frame)
        if stacked is None:
            continue
        action_idx = agent.step(player_id, stacked, r, terminal=False)
        if action_idx is None:
            action_idx = random.randrange(agent.num_actions)
        action_counts[action_idx] += 1
        send_action(conn, action_idx)


print("[TrainingProcess] Starting up...")

server1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server1.bind((HOST, PORT_P1))
server2.bind((HOST, PORT_P2))
server1.listen(1)
server2.listen(1)

with open(READY_FILE, "w") as f:
    f.write("ready")
print("[TrainingProcess] Ports bound, ready file written.")

print("[TrainingProcess] Waiting for Dolphin...")
conn1, _ = server1.accept()
print("[TrainingProcess] P1 connected.")
conn2, _ = server2.accept()
print("[TrainingProcess] P2 connected.")

t1 = threading.Thread(target=player_loop, args=(1, conn1))
t2 = threading.Thread(target=player_loop, args=(2, conn2))
t1.start()
t2.start()
t1.join()
t2.join()
agent.close()