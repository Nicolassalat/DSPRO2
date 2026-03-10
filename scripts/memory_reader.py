# memory_reader.py
# Mario Kart Wii - NTSC-U (RMCE01)
# Confirmed across 3 sessions: base stable, lap offset varies → dynamic scan required

from dolphin import memory

STATIC_PTR = 0x8069FDB4          # always points to 0x80E44BF0
LAP_SCAN_RANGE = (0x100, 0x300)  # lap offset found in this range each session

_base = None
_lap_offset = None

def _find_lap_offset(base):
    for off in range(LAP_SCAN_RANGE[0], LAP_SCAN_RANGE[1], 4):
        try:
            val = memory.read_f32(base + off)
            if 1.0 <= val <= 3.5:
                return off
        except:
            pass
    return None

def init():
    """Call once at race start to lock in the lap offset for this session."""
    global _base, _lap_offset
    _base = memory.read_u32(STATIC_PTR)
    _lap_offset = _find_lap_offset(_base)
    if _lap_offset is None:
        raise RuntimeError("Could not find lap offset — is a race running?")
    print(f"[memory] base=0x{_base:08X} lap_offset=0x{_lap_offset:X}")

def read_lap() -> float:
    """Returns current lap completion (1.0 = start, ~4.0 = finish)."""
    return memory.read_f32(_base + _lap_offset)

def is_initialized() -> bool:
    return _lap_offset is not None