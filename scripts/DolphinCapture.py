# DolphinCapture.py
from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import win32gui
from PIL import Image
import threading


class DolphinCapture:
    def __init__(self, player_id: int, scale: int = 4):
        if player_id not in (1, 2):
            raise ValueError(f"player_id must be 1 or 2, got {player_id}")
        self.player_id = player_id
        self.scale = scale
        self._latest = None
        self._lock = threading.Lock()

        hwnd = self._find_dolphin()
        client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
        _, window_y, _, _ = win32gui.GetWindowRect(hwnd)
        self._crop_top = client_y - window_y

        self._capture = WindowsCapture(
            cursor_capture=False,
            draw_border=False,
            window_name="Mario Kart Wii",
        )
        self._capture.event(self.on_frame_arrived)
        self._capture.event(self.on_closed)

        self._capture.start_free_threaded()
        print(f"[DolphinCapture] Player {player_id} ready.")

    def __call__(self):
        """Return the latest frame, or None if no frame yet."""
        with self._lock:
            return self._latest

    def _find_dolphin(self):
        result = []
        def cb(h, _):
            if "Mario Kart Wii" in win32gui.GetWindowText(h):
                result.append(h)
        win32gui.EnumWindows(cb, None)
        if not result:
            raise RuntimeError("Dolphin window not found.")
        return result[0]

    def on_frame_arrived(self, frame: Frame, capture_control: InternalCaptureControl):
        buf = frame.frame_buffer
        total_h = buf.shape[0]
        client_h = total_h - self._crop_top
        half_h = client_h // 2

        if self.player_id == 1:
            region = buf[self._crop_top : self._crop_top + half_h, :, :3]
        else:
            region = buf[self._crop_top + half_h :, :, :3]

        img = Image.fromarray(region)
        img = img.resize((140, 114), Image.LANCZOS)
        img = img.convert("L")

        with self._lock:
            self._latest = img

    def on_closed(self):
        print(f"[DolphinCapture] Player {self.player_id} capture ended.")