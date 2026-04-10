from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import win32gui
from PIL import Image
import os

OUTPUT_DIR = "C:/mkwii_frames"
os.makedirs(OUTPUT_DIR, exist_ok=True)

frame_count = 0

def find_dolphin():
    result = []
    def cb(h, _):
        if "Mario Kart Wii" in win32gui.GetWindowText(h):
            result.append(h)
    win32gui.EnumWindows(cb, None)
    return result[0] if result else None

hwnd = find_dolphin()
client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
window_x, window_y, _, _ = win32gui.GetWindowRect(hwnd)
crop_top = client_y - window_y  # title bar height in pixels

capture = WindowsCapture(
    cursor_capture=False,
    draw_border=False,
    window_name="Mario Kart Wii",  # partial match is fine
)

@capture.event
def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
    global frame_count
    frame_count += 1
    if frame_count % 30 != 0:
        return
    img = Image.fromarray(frame.frame_buffer[crop_top:, :, :3])  # crop title bar
    img = img.resize((img.width // 4, img.height // 4), Image.LANCZOS)
    img = img.convert("L")
    img.save(f"{OUTPUT_DIR}/frame_{frame_count:08d}.png")
    print(f"Saved frame {frame_count}")
    frame_count += 1

@capture.event
def on_closed():
    print("Capture ended")

capture.start()