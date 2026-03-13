from dolphin import memory

# PAL (RMCP01) static pointers
_RACE_INFO_PTR  = 0x809BD730
_STAGE_INFO_PTR = 0x809C18F8

_race_base  = None
_stage_base = None

def init():
    global _race_base, _stage_base
    _race_base  = memory.read_u32(_RACE_INFO_PTR)
    _stage_base = memory.read_u32(_STAGE_INFO_PTR)
    print(f"[memory] race_base=0x{_race_base:08X} stage_base=0x{_stage_base:08X}")

def read_lap() -> float:
    """1.0 at race start, ~4.0 at finish (3-lap race)."""
    return memory.read_f32(_race_base + 0xF8)

def read_max_lap() -> float:
    """Highest lap completion reached — never decreases."""
    return memory.read_f32(_race_base + 0xFC)

def read_stage() -> int:
    """0 = intro camera, 1 = countdown, 2 = racing."""
    return memory.read_u8(_stage_base + 0x2B)

def is_racing() -> bool:
    return read_stage() == 2

def is_initialized() -> bool:
    return _race_base is not None