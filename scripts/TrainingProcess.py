# TrainingProcess.py
import socket, struct, json, threading, os, time, random

from DolphinCapture import DolphinCapture
from RewardFunction import compute_reward
from neural_agent import NeuralAgent

HOST       = "127.0.0.1"
PORT_P1    = 55001
PORT_P2    = 55002
READY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "training_ready.txt")

agent = NeuralAgent(num_actions=15)


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

def make_capture(player_id, retries=20, delay=10.0):
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
    episode_num = 0

    while True:
        try:
            msg = recv_json(conn)
        except ConnectionResetError:
            break

        if msg.get("reset"):
            stuck = msg.get("stuck", False)
            r = compute_reward({}, progress_delta=0.0, done=not stuck, stuck=stuck)
            episode_reward += r
            episode_num += 1
            print(f"[TrainingProcess] P{player_id} episode end. stuck={stuck} total_reward={episode_reward:.2f}")
            agent.writer.add_scalar(f"episode/P{player_id}_reward", episode_reward, episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_length", episode_steps, episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_stuck", int(stuck), episode_num)
            agent.writer.add_scalar(f"episode/P{player_id}_progress", last_rc, episode_num)
            last_rc = 1.0
            episode_reward = 0.0
            episode_steps = 0
            continue

        if msg.get("done"):
            snap = msg.get("snapshot", {})
            r = compute_reward(snap, progress_delta=0.0, done=True, stuck=False)
            episode_reward += r
            frame = cap()
            agent.step(player_id, frame, r, terminal=True)
            continue

        snap = msg["snapshot"]
        frame = cap()
        rc = snap["race_completion"]
        progress_delta = rc - last_rc
        last_rc = rc
        r = compute_reward(snap, progress_delta, done=False, stuck=False)
        episode_reward += r
        episode_steps += 1
        action_idx = agent.step(player_id, frame, r, terminal=False)
        if action_idx is None:
            action_idx = random.randrange(agent.num_actions)
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