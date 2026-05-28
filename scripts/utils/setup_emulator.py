# setup_emulator.py
import urllib.request, os, platform, shutil
import py7zr

RELEASE_URL = "https://github.com/Felk/dolphin/releases/download/scripting-preview4/dolphin-scripting-preview4-x64.7z"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_dolphin_dir():
    if platform.system() == "Windows":
        print("This is a Windows system")
        return os.path.join(os.environ["APPDATA"], "Dolphin Emulator")
    else:
        raise RuntimeError("Unsupported OS for automatic Dolphin setup.")

if platform.system() == "Windows":
    SAVE_DST = os.path.join(get_dolphin_dir(), "Wii", "title",
                        "00010004", "524d4350", "data", "rksys.dat")
    emulator_dir = os.path.join(PROJECT_ROOT, "emulator")
    os.makedirs(emulator_dir, exist_ok=True)
    archive_path = os.path.join(emulator_dir, "dolphin.7z")
    print("Downloading Felk's Dolphin...")
    urllib.request.urlretrieve(RELEASE_URL, archive_path)
    print("Extracting...")
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        z.extractall(emulator_dir)
    os.remove(archive_path)
    print("Done. Dolphin is at emulator/")
    print("Installing MKW save file...")
    os.makedirs(os.path.dirname(SAVE_DST), exist_ok=True)
    shutil.copy(os.path.join(PROJECT_ROOT, "assets", "rksys.dat"), SAVE_DST)
    print("Done, Dolphin is ready!.")

elif platform.system() == "Darwin":
    print("There is no macOS build of Felk's Dolphin. Please build it yourself from the source code.")

else:
    print("There is no Linux build of Felk's Dolphin. Please build it yourself from the source code.")