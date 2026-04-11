#DolphinEnv.py
import socket
from dolphin import event

print("[DolphinEnv] Trying to connect...")
try:
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect(("127.0.0.1", 55001))
    print("[DolphinEnv] P1 connected.")
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect(("127.0.0.1", 55002))
    print("[DolphinEnv] P2 connected.")
    s1.sendall(b"hello")
    s2.sendall(b"hello")
    print("[DolphinEnv] Sent.")
except Exception as e:
    print(f"[DolphinEnv] Error: {e}")

@event.on_frameadvance
def on_frame():
    pass