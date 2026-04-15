# open_dolphin.py
import os, platform

if platform.system() == "Windows":
    os.startfile(os.path.join(os.path.dirname(os.path.dirname(__file__)), "emulator", "Dolphin.exe"))

else:
    print("Automatic Dolphin launch is only supported on Windows. Please launch it manually.")