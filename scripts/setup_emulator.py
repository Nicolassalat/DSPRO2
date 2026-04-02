# setup_emulator.py
import urllib.request, os, platform, shutil
import py7zr

RELEASE_URL = "https://github.com/Felk/dolphin/releases/download/scripting-preview4/dolphin-scripting-preview4-x64.7z"

def get_dolphin_dir():
    if platform.system() == "Windows":
        print("This is a Windows system")
        return os.path.join(os.environ["APPDATA"], "Dolphin Emulator")
    
    elif platform.system() == "Darwin":
        print("This is a macOS system")
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Dolphin")
    
    else:
        print("This is a Linux system")
        return os.path.expanduser("~/.local/share/dolphin-emu")
    
SAVE_DST = os.path.join(get_dolphin_dir(), "Wii", "title",
                        "00010004", "524d4350", "data", "rksys.dat")

os.makedirs("emulator", exist_ok=True)
print("Downloading Felk's Dolphin...")
urllib.request.urlretrieve(RELEASE_URL, "emulator/dolphin.7z")
print("Extracting...")
with py7zr.SevenZipFile("emulator/dolphin.7z", mode='r') as z:
    z.extractall("emulator/")
os.remove("emulator/dolphin.7z")
print("Done. Dolphin is at emulator/")
print("Installing MKW save file...")
os.makedirs(os.path.dirname(SAVE_DST), exist_ok=True)
shutil.copy(os.path.join("assets", "rksys.dat"), SAVE_DST)
print("Done, Dolphin is ready!.")