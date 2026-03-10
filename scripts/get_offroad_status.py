from dolphin import event, memory

BASE = 0x80E44BF0

# Offsets from base to our surface candidates
OFFSETS = [0x913E, 0x9146, 0x9533, 0xA87A, 0xA887, 0xA17A, 0xEF99]

async def main():
    frame = 0
    while True:
        await event.frameadvance()
        frame += 1
        if frame % 15 != 0:
            continue
        vals = []
        for off in OFFSETS:
            v = memory.read_u8(BASE + off)
            vals.append(f"+0x{off:X}={v}")
        print(" | ".join(vals))

await main()