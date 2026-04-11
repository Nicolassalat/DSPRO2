#TrainingProcess.py
import socket, struct, json, threading, os, random, time
from DolphinCapture import DolphinCapture

HOST      = "127.0.0.1"
PORT_P1   = 55001
PORT_P2   = 55002
READY_FILE = os.path.join(os.getcwd(), "training_ready.txt")

class agent:
    @staticmethod
    def get_action(frame, player_id):
        return random.randint(0, 13)

class reward:
    @staticmethod
    def reward_for_frame(snapshot, player_id):
        return 0.0

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

    while True:
        msg = recv_json(conn)
        if msg is None:
            break
        if msg.get("reset"):
            print(f"[TrainingProcess] P{player_id} episode reset.")
            continue
        if msg.get("done"):
            print(f"[TrainingProcess] P{player_id} finished.")
            continue

        snap  = msg["snapshot"]
        frame = cap()
        r = reward.reward_for_frame(snap, player_id)
        action_idx = agent.get_action(frame, player_id)
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