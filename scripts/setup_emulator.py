# setup_emulator.py
import urllib.request, os
import py7zr

RELEASE_URL = "https://github.com/Felk/dolphin/releases/download/scripting-preview4/dolphin-scripting-preview4-x64.7z"

os.makedirs("emulator", exist_ok=True)
print("Downloading Felk's Dolphin...")
urllib.request.urlretrieve(RELEASE_URL, "emulator/dolphin.7z")
print("Extracting...")
with py7zr.SevenZipFile("emulator/dolphin.7z", mode='r') as z:
    z.extractall("emulator/DolphinFelk")
os.remove("emulator/dolphin.7z")
os.remove("emulator/dolphin.zip")
print("Done. Dolphin is at emulator/DolphinFelk/")