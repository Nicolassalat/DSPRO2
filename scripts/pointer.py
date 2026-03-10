from dolphin import event, memory

STATIC_PTR = 0x8069FDB4

def find_lap_offset(base):
    for off in range(0x100, 0x300, 4):
        try:
            val = memory.read_f32(base + off)
            if 1.0 <= val <= 3.5:
                return off
        except:
            pass
    return None

async def main():
    lap_offset = None
    while lap_offset is None:
        await event.frameadvance()
        base = memory.read_u32(STATIC_PTR)
        if 0x80000000 <= base <= 0x81800000:
            lap_offset = find_lap_offset(base)
    
    base = memory.read_u32(STATIC_PTR)
    print(f"Session: base=0x{base:08X} | lap_offset=0x{lap_offset:X}")
    
    frame = 0
    while True:
        await event.frameadvance()
        frame += 1
        if frame % 60 != 0:
            continue
        base = memory.read_u32(STATIC_PTR)
        lap = memory.read_f32(base + lap_offset)
        print(f"lap={lap:.4f}")

await main()