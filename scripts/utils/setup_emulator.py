# setup_emulator.py
import urllib.request, os, platform, shutil, zipfile
import py7zr

RELEASE_URL   = "https://github.com/Felk/dolphin/releases/download/scripting-preview4/dolphin-scripting-preview4-x64.7z"
GAME_DATA_URL = "https://github.com/Nicolassalat/DSPRO2/releases/download/v1.0-data/game_data.zip"
PROJECT_ROOT  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    print("Downloading game data (save states + assets)...")
    game_data_path = os.path.join(emulator_dir, "game_data.zip")
    urllib.request.urlretrieve(GAME_DATA_URL, game_data_path)
    print("Extracting game data...")
    with zipfile.ZipFile(game_data_path, 'r') as z:
        z.extractall(PROJECT_ROOT)
    os.remove(game_data_path)
    print("Done, game data is ready.")

elif platform.system() == "Darwin":
    print("There is no macOS build of Felk's Dolphin. Please build it yourself from the source code.")

else:
    print("There is no Linux build of Felk's Dolphin. Please build it yourself from the source code.")