import glob
import os
import cv2
from pathlib import Path

# FOLDER = r"C:\Users\thomas.ewald\AppData\Roaming\Dolphin Emulator\Dump\Frames"
FOLDER = Path.home() / "AppData" / "Roaming" / "Dolphin Emulator" / "Dump" / "Frames"

def get_latest_avi(folder: str) -> str | None:
    pattern = folder / "*.avi" # frame dumps are stored as .avi
    files = glob.glob(str(pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def process_video(path: str, scale: float = 0.25, to_gray: bool = True):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    print(f"Processing: {path}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # downscale to 1/4 size
        h, w = frame.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        frame_small = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # convert to grayscale
        if to_gray:
            frame_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

        # for now I will just diplay the file [TODO: write back into desired format]
        cv2.imshow("dolphin_dump", frame_small)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    latest = get_latest_avi(FOLDER)
    if latest is None:
        print("No AVI files found.")
    else:
        process_video(latest)
