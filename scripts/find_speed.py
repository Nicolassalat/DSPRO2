from dolphin import event, memory
import math

print("[diag] Script loaded!")
print("[diag] Will wait 600 frames (~10s), then read positions every 30 frames.")
print("[diag] Make sure you're racing when the scan starts.")

POS_PTR = 0x809C2EF8  # PAL pointer — may be wrong for NTSC-U

async def main():
    print("[diag] Waiting 600 frames...")
    for i in range(600):
        if i % 120 == 0:
            print(f"[diag] ...waiting ({i}/600)")
        await event.frameadvance()

    print("[diag] === SCAN STARTED ===")

    prev_pos = None
    frame = 0

    while True:
        await event.frameadvance()
        frame += 1
        if frame % 30 != 0:
            continue

        try:
            base = memory.read_u32(POS_PTR)
        except Exception as e:
            print(f"[diag] pointer read FAILED: {e}")
            continue

        if not (0x80000000 <= base <= 0x81800000):
            print(f"[diag] base out of range: 0x{base:08X}")
            continue

        # Try reading XYZ at the documented PAL offsets
        try:
            x = memory.read_f32(base + 0x40)
            y = memory.read_f32(base + 0x44)
            z = memory.read_f32(base + 0x48)
        except Exception as e:
            print(f"[diag] position read FAILED at base=0x{base:08X}: {e}")
            continue

        # Compute speed from delta if we have a previous position
        speed = 0.0
        if prev_pos is not None:
            dx = x - prev_pos[0]
            dy = y - prev_pos[1]
            dz = z - prev_pos[2]
            speed = math.sqrt(dx*dx + dy*dy + dz*dz)

        print(f"[diag] base=0x{base:08X}  x={x:.2f} y={y:.2f} z={z:.2f}  speed={speed:.4f}")
        prev_pos = (x, y, z)

        # Every 150 frames, also dump a few nearby offsets to see what's around
        if frame % 150 == 0:
            print("[diag] --- offset dump around +0x00 to +0x60 ---")
            for off in range(0x00, 0x64, 4):
                try:
                    val = memory.read_f32(base + off)
                    if val == val:  # skip NaN
                        print(f"  +0x{off:02X} = {val:.4f}")
                except:
                    pass
            print("[diag] --- end dump ---")

await main()