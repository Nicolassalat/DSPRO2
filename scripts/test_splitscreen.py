"""
Verify ALL of Tango's memory addresses on PAL for P1 and P2.
Run in a split screen race. Drive around, do drifts, wheelies, use mushrooms,
go off-road, hit walls, go off a ramp — try to trigger everything.

./emulator/Dolphin.exe --script verify_all_memory.py
"""

from dolphin import event, memory, gui, savestate

SAVE_STATE_PATH = r"C:\Users\nicol\Documents\Schule\DSPRO2\DSPRO2\save_states\start_lc_splitscreen_2p.sav"

def resolve(base, offsets):
    current = memory.read_u32(base)
    for off in offsets:
        addr = current + off
        current = memory.read_u32(addr)
    return addr

def read_safe_f32(addr):
    try:
        return memory.read_f32(addr)
    except:
        return "FAIL"

def read_safe_u32(addr):
    try:
        return memory.read_u32(addr)
    except:
        return "FAIL"

def read_safe_u16(addr):
    try:
        return memory.read_u16(addr)
    except:
        return "FAIL"

def read_safe_u8(addr):
    try:
        return memory.read_u8(addr)
    except:
        return "FAIL"

# All pointer chains from Tango's Memory class
# Format: (name, base, offsets, read_type)
# player_dependent: True means the second offset is player_id * 4

RACE_MANAGER_ADDRS = [
    ("RaceCompletion",   0x809BD730, [0xC, "PLAYER", 0xC],    "f32"),
    ("currentLap",       0x809BD730, [0xC, "PLAYER", 0x24],   "u16"),
    ("countdownTimer",   0x809BD730, [0x22],                    "u16"),
    ("stage",            0x809BD730, [0x28],                    "u32"),
]

KART_ADDRS = [
    # KartMove
    ("speed",              0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x20],    "f32"),
    ("acceleration",       0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x30],    "f32"),
    ("offroadInvincibility", 0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x148], "u16"),
    ("wheelieFrames",      0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x2A8],   "u16"),
    ("wheelieCooldown",    0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x2B6],   "u16"),
    ("leanRot",            0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x294],   "f32"),
    ("softSpeedLimit",     0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x18],    "f32"),
    ("miniturboCharge",    0x809C18F8, [0x20, "PLAYER", 0x44, 0xFE],         "u16"),
    ("mt_boost_timer",     0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x102],   "u16"),
    ("allmt",              0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x10C],   "u16"),
    ("mush_and_boost",     0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x110],   "u16"),

    # KartDynamics
    ("positionX",          0x809C18F8, [0x20, "PLAYER", 0x0, 0x8, 0x90, 0x18],       "f32"),
    ("positionY",          0x809C18F8, [0x20, "PLAYER", 0x0, 0x8, 0x90, 0x1C],       "f32"),
    ("positionZ",          0x809C18F8, [0x20, "PLAYER", 0x0, 0x8, 0x90, 0x20],       "f32"),

    # KartState
    ("bitfield2",          0x809C18F8, [0x20, "PLAYER", 0x0, 0x4, 0xC],              "u32"),
    ("airtime",            0x809C18F8, [0x20, "PLAYER", 0x0, 0x4, 0x1C],             "u16"),
    ("trickableTimer",     0x809C18F8, [0x20, "PLAYER", 0x0, 0x4, 0xA6],             "u16"),

    # KartCollide
    ("surfaceFlags",       0x809C18F8, [0x20, "PLAYER", 0x0, 0x18, 0x18, 0x2C],      "u32"),
    ("floor_collision_count", 0x809C18F8, [0x20, "PLAYER", 0x0, 0x18, 0x40],         "u16"),
    ("race_position",      0x809C18F8, [0x20, "PLAYER", 0x0, 0x18, 0x3C],            "u8"),
    ("respawn_timer",      0x809C18F8, [0x20, "PLAYER", 0x0, 0x18, 0x18, 0x48],      "u16"),
    ("wall_collide",       0x809C18F8, [0x20, "PLAYER", 0x0, 0x8, 0x90, 0x8, 0x8],   "u32"),

    # Trick
    ("trick_cooldown",     0x809C18F8, [0x20, "PLAYER", 0x0, 0x28, 0x258, 0x38],     "u16"),
    ("hopPos",             0x809C18F8, [0x20, "PLAYER", 0x44, 0x22C],                 "f32"),
]

MISC_ADDRS = [
    ("mushroomCount",      0x809C3618, [0x14, 0x90],                                  "u32"),
]

def resolve_with_player(base, offsets, player_id):
    """Resolve pointer chain, replacing 'PLAYER' with player_id * 4."""
    resolved = []
    for off in offsets:
        if off == "PLAYER":
            resolved.append(player_id * 4)
        else:
            resolved.append(off)
    return resolve(base, resolved)

def read_value(addr, read_type):
    if read_type == "f32":
        return read_safe_f32(addr)
    elif read_type == "u32":
        return read_safe_u32(addr)
    elif read_type == "u16":
        return read_safe_u16(addr)
    elif read_type == "u8":
        return read_safe_u8(addr)
    return "???"

def format_value(val, read_type):
    if val == "FAIL":
        return "FAIL"
    if read_type == "f32":
        return f"{val:12.4f}"
    elif read_type == "u32":
        return f"0x{val:08X}"
    elif read_type == "u16":
        return f"{val:6d}"
    elif read_type == "u8":
        return f"{val:4d}"
    return str(val)

async def main():
    print("=== COMPREHENSIVE MEMORY VERIFICATION ===")

    print(f"Loading save state...")
    savestate.load_from_file(SAVE_STATE_PATH)

    print("Drive around! Do drifts, wheelies, mushrooms, go off-road, hit walls.")
    print("")

    frame = 0
    while True:
        await event.frameadvance()
        frame += 1
        if frame % 120 != 0:
            continue

        print(f"===== Frame {frame} =====")

        # Race manager (shared, not per-player)
        print("-- Race Manager (shared) --")
        for name, base, offsets, rtype in RACE_MANAGER_ADDRS:
            if "PLAYER" in offsets:
                for pid in [0, 1]:
                    try:
                        addr = resolve_with_player(base, offsets, pid)
                        val = read_value(addr, rtype)
                        print(f"  P{pid+1} {name:25s} = {format_value(val, rtype)}")
                    except Exception as e:
                        print(f"  P{pid+1} {name:25s} = RESOLVE FAIL ({e})")
            else:
                try:
                    addr = resolve(base, offsets)
                    val = read_value(addr, rtype)
                    print(f"     {name:25s} = {format_value(val, rtype)}")
                except Exception as e:
                    print(f"     {name:25s} = RESOLVE FAIL ({e})")

        # Kart addresses (per-player)
        print("-- Kart (per-player) --")
        for name, base, offsets, rtype in KART_ADDRS:
            for pid in [0, 1]:
                try:
                    addr = resolve_with_player(base, offsets, pid)
                    val = read_value(addr, rtype)
                    print(f"  P{pid+1} {name:25s} = {format_value(val, rtype)}")
                except Exception as e:
                    print(f"  P{pid+1} {name:25s} = RESOLVE FAIL ({e})")

        # Misc (not per-player, or needs separate investigation)
        print("-- Misc --")
        for name, base, offsets, rtype in MISC_ADDRS:
            try:
                addr = resolve(base, offsets)
                val = read_value(addr, rtype)
                print(f"     {name:25s} = {format_value(val, rtype)}")
            except Exception as e:
                print(f"     {name:25s} = RESOLVE FAIL ({e})")

        print("")

await main()