# evaluate.py
import argparse
import numpy as np
import socket, struct, json, threading, os, time, sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/

from env.dolphin_capture import DolphinCapture
from env.reward_function import advanced_reward
from train.neural_agent import NeuralAgent

HOST       = "127.0.0.1"
PORT_P1    = 55001
PORT_P2    = 55002
READY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "training_ready.txt")
FRAME_STACK = 4

parser = argparse.ArgumentParser()
parser.add_argument("--model", default=None, help="Path to agent_model.pth")
parser.add_argument("--episodes", type=int, default=20)
args = parser.parse_args()

agent = NeuralAgent(num_actions=15, model_path=args.model)
agent.steps_done = 10_000_000  # eps = max(0, 1 - 10M/50k) = 0 → pure greedy

frame_buffers = {1: deque(maxlen=FRAME_STACK), 2: deque(maxlen=FRAME_STACK)}


def get_stacked_frame(player_id, new_frame):
    if new_frame is None:
        return None
    buf = frame_buffers[player_id]
    buf.append(np.array(new_frame, dtype=np.float32))
    while len(buf) < FRAME_STACK:
        buf.append(np.array(new_frame, dtype=np.float32))
    return np.stack(list(buf), axis=0)


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
            print(f"[Evaluate] Dolphin window not ready, retry {i+1}/{retries}...")
            time.sleep(delay)
    raise RuntimeError("Dolphin window never appeared.")


def player_loop(player_id, conn, results):
    cap = make_capture(player_id)
    episode_num = 0
    episode_reward = 0.0
    last_rc = 1.0
    rewards = []
    finishes = 0

    while episode_num < args.episodes:
        try:
            msg = recv_json(conn)
        except (ConnectionResetError, OSError):
            break
        if msg is None:
            break

        if msg.get("reset"):
            stuck = msg.get("stuck", False)
            finished = not stuck
            if finished:
                finishes += 1
            rewards.append(episode_reward)
            episode_num += 1
            print(f"[Evaluate] P{player_id} ep {episode_num}/{args.episodes}  finished={finished}  reward={episode_reward:.2f}")
            frame_buffers[player_id].clear()
            episode_reward = 0.0
            last_rc = 1.0
            continue

        if msg.get("done"):
            finishes += 1
            rewards.append(episode_reward)
            episode_num += 1
            print(f"[Evaluate] P{player_id} ep {episode_num}/{args.episodes}  finished=True  reward={episode_reward:.2f}")
            episode_reward = 0.0
            last_rc = 1.0
            continue

        snap = msg["snapshot"]
        frame = cap()
        rc = snap["race_completion"]
        progress_delta = rc - last_rc
        last_rc = rc
        episode_reward += advanced_reward(snap, progress_delta, done=False, stuck=False)

        stacked = get_stacked_frame(player_id, frame)
        if stacked is None:
            continue
        action_idx = agent.select_action(stacked)
        send_action(conn, action_idx)

    results[player_id] = {
        "episodes":    episode_num,
        "finish_rate": finishes / max(episode_num, 1),
        "avg_reward":  sum(rewards) / max(len(rewards), 1),
        "best_reward": max(rewards) if rewards else 0.0,
    }
    print(
        f"[Evaluate] P{player_id} COMPLETE — "
        f"finish_rate={results[player_id]['finish_rate']:.1%}  "
        f"avg_reward={results[player_id]['avg_reward']:.2f}  "
        f"best={results[player_id]['best_reward']:.2f}"
    )


print("[Evaluate] Starting up...")

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
print("[Evaluate] Ports bound, ready file written.")
print("[Evaluate] Waiting for Dolphin...")

conn1, _ = server1.accept()
print("[Evaluate] P1 connected.")
conn2, _ = server2.accept()
print("[Evaluate] P2 connected.")

results = {}
t1 = threading.Thread(target=player_loop, args=(1, conn1, results))
t2 = threading.Thread(target=player_loop, args=(2, conn2, results))
t1.start()
t2.start()
t1.join()
t2.join()

print("\n" + "=" * 52)
print(f"  EVALUATION COMPLETE  ({args.episodes} episodes per player)")
print("=" * 52)
for pid in [1, 2]:
    r = results.get(pid, {})
    print(
        f"  P{pid}: finish_rate={r.get('finish_rate', 0):.1%}  "
        f"avg_reward={r.get('avg_reward', 0):.2f}  "
        f"best={r.get('best_reward', 0):.2f}"
    )
print("=" * 52)

agent.close()
