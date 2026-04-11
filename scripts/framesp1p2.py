import os
import threading
from DolphinCapture import DolphinCapture

P1_DIR = r"C:\Users\Nicolas\LocalDocuments\HSLU\DSPRO2\P1frames"
P2_DIR = r"C:\Users\Nicolas\LocalDocuments\HSLU\DSPRO2\P2frames"
os.makedirs(P1_DIR, exist_ok=True)
os.makedirs(P2_DIR, exist_ok=True)

p1_count = 0
p2_count = 0

cap1 = DolphinCapture(player_id=1, every_n=30)
cap2 = DolphinCapture(player_id=2, every_n=30)

@cap1.on_frame
def handle_p1(img):
    global p1_count
    p1_count += 1
    path = os.path.join(P1_DIR, f"frame_{p1_count:08d}.png")
    img.save(path)
    print(f"[P1] Saved frame {p1_count}")

@cap2.on_frame
def handle_p2(img):
    global p2_count
    p2_count += 1
    path = os.path.join(P2_DIR, f"frame_{p2_count:08d}.png")
    img.save(path)
    print(f"[P2] Saved frame {p2_count}")

t1 = threading.Thread(target=cap1.start)
t2 = threading.Thread(target=cap2.start)
t1.start()
t2.start()
t1.join()
t2.join()