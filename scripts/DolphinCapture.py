from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import win32gui
from PIL import Image


class DolphinCapture:
    """Captures grayscale frames for one player from a split-screen Dolphin window."""

    def __init__(self, player_id: int, scale: int = 4, every_n: int = 1):
        if player_id not in (1, 2):
            raise ValueError(f"player_id must be 1 or 2, got {player_id}")
        self.player_id = player_id
        self.scale = scale
        self.every_n = every_n
        self._frame_count = 0
        self._on_frame = None

        hwnd = self._find_dolphin()
        client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
        _, window_y, _, _ = win32gui.GetWindowRect(hwnd)
        self._crop_top = client_y - window_y

        self._capture = WindowsCapture(
            cursor_capture=False,
            draw_border=False,
            window_name="Mario Kart Wii",
        )
        def on_frame_arrived(frame, capture_control):
            self._on_frame_arrived(frame, capture_control)

        def on_closed():
            self._on_closed()

        self._capture.event(on_frame_arrived)
        self._capture.event(on_closed)
        print(f"[DolphinCapture] Player {player_id} ready.")

    def on_frame(self, fn):
        """Register a callback: fn(img: PIL.Image)"""
        self._on_frame = fn
        return fn

    def start(self):
        self._capture.start()

    def _find_dolphin(self):
        result = []
        def cb(h, _):
            if "Mario Kart Wii" in win32gui.GetWindowText(h):
                result.append(h)
        win32gui.EnumWindows(cb, None)
        if not result:
            raise RuntimeError("Dolphin window not found.")
        return result[0]

    def _on_frame_arrived(self, frame: Frame, capture_control: InternalCaptureControl):
        self._frame_count += 1
        if self._frame_count % self.every_n != 0:
            return

        buf = frame.frame_buffer
        total_h = buf.shape[0]
        client_h = total_h - self._crop_top
        half_h = client_h // 2

        if self.player_id == 1:
            region = buf[self._crop_top : self._crop_top + half_h, :, :3]
        else:
            region = buf[self._crop_top + half_h :, :, :3]

        img = Image.fromarray(region)
        img = img.resize((img.width // self.scale, img.height // self.scale), Image.LANCZOS)
        img = img.convert("L")

        if self._on_frame:
            self._on_frame(img)

    def _on_closed(self):
        print(f"[DolphinCapture] Player {self.player_id} capture ended.")