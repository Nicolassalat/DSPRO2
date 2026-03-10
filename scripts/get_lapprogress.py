import sys, os
# From emulator/DolphinFelk/ go up two levels to repo root, then into scripts/
sys.path.insert(0, os.path.join(os.getcwd(), "..", "..", "scripts"))

import memory_reader
from dolphin import event

print("Waiting for race...")

async def main():
    frame = 0
    while True:
        await event.frameadvance()
        if not memory_reader.is_initialized():
            try:
                memory_reader.init()
            except:
                pass
            continue
        
        frame += 1
        if frame % 60 != 0:
            continue
        lap = memory_reader.read_lap()
        print(f"lap={lap:.4f}")

await main()