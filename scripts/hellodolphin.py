# hellodolphin.py

'''
how to talk to dolphin from a script running inside dolphin itself. this is just a test to make sure the event system works and we can print something every second.
'''
from dolphin import event

frame_count = 0

print("Hello, Mario Kart Wii!")

@event.on_frameadvance
def on_frame():
    global frame_count
    frame_count += 1
    if frame_count % 60 == 0:  # once per second
        print(f"[MKWii] Frame count: {frame_count}")
