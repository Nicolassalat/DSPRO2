from dolphin import event, memory

frame_count = 0

print("Hello, Mario Kart Wii!")

@event.on_frameadvance
def on_frame():
    global frame_count
    frame_count += 1
    if frame_count % 60 == 0:  # once per second
        print(f"[MKWii] Frame count: {frame_count}")
