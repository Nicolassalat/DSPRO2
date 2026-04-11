# game_memory.py
"""
Reads MKWii game state from RAM using the Dolphin scripting API.
Only works for PAL (RMCP01). 
Pointers confirmed working (finally) as of Mar 2025.
"""

from dolphin import memory


def _resolve(base, offsets):
    # Walks a multi-level pointer chain. Returns the final address (not value).
    current = memory.read_u32(base)
    for off in offsets:
        addr = current + off
        current = memory.read_u32(addr)
    return addr


# Base pointers for RMCP01 (PAL)
RACE_MANAGER = 0x809BD730
KART_OBJECT  = 0x809C18F8
ITEM_HOLDER  = 0x809C3618


class GameMemory:
    def __init__(self, player_id=0):
        # 0 for P1, 1 for P2. 
        # Note: P2 hasn't been tested as much, but the offset is supposed to be 0x4
        self.pid = player_id
        self._poff = player_id * 4   

    def _kart(self, offsets, read_fn):
        # Helper to inject player offset and resolve kart pointers
        resolved = [self._poff if o == "P" else o for o in offsets]
        addr = _resolve(KART_OBJECT, resolved)
        return read_fn(addr)

    def _race(self, offsets, read_fn):
        # Helper for race manager pointers
        resolved = [self._poff if o == "P" else o for o in offsets]
        addr = _resolve(RACE_MANAGER, resolved)
        return read_fn(addr)

    # --- Race Manager ---

    def race_completion(self):
        # ~1.0 at start, 2