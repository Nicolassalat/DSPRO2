# game_memory.py
"""
GameMemory: reads all MKWii game state from RAM via Dolphin scripting API.
PAL (RMCP01) only. All pointer chains confirmed working 2025-03-19.

Usage inside a Dolphin script:
    from game_memory import GameMemory
    mem = GameMemory(player_id=0)  # 0=P1, 1=P2
    print(mem.speed())
    print(mem.race_completion())
"""

from dolphin import memory


# ---------------------------------------------------------------------------
# Pointer resolution
# ---------------------------------------------------------------------------

def _resolve(base, offsets):
    """Walk a pointer chain. Returns the final ADDRESS (not value)."""
    current = memory.read_u32(base)
    for off in offsets:
        addr = current + off
        current = memory.read_u32(addr)
    return addr


# ---------------------------------------------------------------------------
# Base pointers (PAL RMCP01)
# ---------------------------------------------------------------------------

_RACE_MANAGER = 0x809BD730
_KART_OBJECT  = 0x809C18F8
_ITEM_HOLDER  = 0x809C3618


# ---------------------------------------------------------------------------
# GameMemory
# ---------------------------------------------------------------------------

class GameMemory:
    """Read-only interface to MKWii game memory for one player."""

    def __init__(self, player_id=0):
        """
        player_id: 0 for P1, 1 for P2.
        The player offset (player_id * 4) is injected into pointer chains
        at the position marked below.
        """
        self.pid = player_id
        self._poff = player_id * 4   # 0x0 for P1, 0x4 for P2

    # -- helpers ----------------------------------------------------------

    def _kart(self, offsets, read_fn):
        """Resolve a kart pointer chain and read with read_fn."""
        resolved = [self._poff if o == "P" else o for o in offsets]
        addr = _resolve(_KART_OBJECT, resolved)
        return read_fn(addr)

    def _race(self, offsets, read_fn):
        """Resolve a race-manager pointer chain and read with read_fn."""
        resolved = [self._poff if o == "P" else o for o in offsets]
        addr = _resolve(_RACE_MANAGER, resolved)
        return read_fn(addr)

    # =====================================================================
    # Race Manager (0x809BD730)
    # =====================================================================

    def race_completion(self):
        """Float: ~1.0 at start, 2.0 = end lap 1, 3.0 = end lap 2, 4.0 = finish."""
        return self._race([0xC, "P", 0xC], memory.read_f32)

    def current_lap(self):
        """u16: 0 during countdown, 1/2/3 during race."""
        return self._race([0xC, "P", 0x24], memory.read_u16)

    def stage(self):
        """u32: 1=countdown, 2=racing, 4=finished. Shared across all players."""
        addr = _resolve(_RACE_MANAGER, [0x28])
        return memory.read_u32(addr)

    def countdown_timer(self):
        """u16: counts up in frames from race start. Shared across all players."""
        addr = _resolve(_RACE_MANAGER, [0x22])
        return memory.read_u16(addr)

    # =====================================================================
    # KartMove
    # =====================================================================

    def speed(self):
        """Float: current speed. ~70-82 on-road, ~3-30 off-road, 115 mushroom boost, 0 stopped."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x20], memory.read_f32)

    def acceleration(self):
        """Float: current acceleration value."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x30], memory.read_f32)

    def soft_speed_limit(self):
        """Float: current speed cap. Drops when off-road, 115 during mushroom boost."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x18], memory.read_f32)

    def offroad_invincibility(self):
        """u16: frames remaining of mushroom off-road immunity. 0 = normal."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x148], memory.read_u16)

    def wheelie_frames(self):
        """u16: frames the current wheelie has been active. 0 = not wheeling."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x2A8], memory.read_u16)

    def wheelie_cooldown(self):
        """u16: frames until wheelie can be performed again."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x2B6], memory.read_u16)

    def lean_rot(self):
        """Float: lean rotation. -1.0 to 1.0, indicates turning direction."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x294], memory.read_f32)

    def miniturbo_charge(self):
        """u16: drift charge level. Increases while drifting, resets on release."""
        return self._kart([0x20, "P", 0x44, 0xFE], memory.read_u16)

    def mt_boost_timer(self):
        """u16: frames remaining of mini-turbo boost after releasing drift."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x102], memory.read_u16)

    def allmt(self):
        """u16: combined boost timer (all mini-turbo sources)."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x10C], memory.read_u16)

    def mush_and_boost(self):
        """u16: mushroom/boost pad timer. Counts down from ~59."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x110], memory.read_u16)

    # =====================================================================
    # KartDynamics (world position)
    # =====================================================================

    def position_x(self):
        """Float: world X coordinate."""
        return self._kart([0x20, "P", 0x0, 0x8, 0x90, 0x18], memory.read_f32)

    def position_y(self):
        """Float: world Y coordinate (height)."""
        return self._kart([0x20, "P", 0x0, 0x8, 0x90, 0x1C], memory.read_f32)

    def position_z(self):
        """Float: world Z coordinate."""
        return self._kart([0x20, "P", 0x0, 0x8, 0x90, 0x20], memory.read_f32)

    def position(self):
        """Tuple (x, y, z) of world coordinates."""
        return (self.position_x(), self.position_y(), self.position_z())

    # =====================================================================
    # KartState
    # =====================================================================

    def bitfield2(self):
        """u32: kart state bitfield."""
        return self._kart([0x20, "P", 0x0, 0x4, 0xC], memory.read_u32)

    def airtime(self):
        """u16: frames spent in the air."""
        return self._kart([0x20, "P", 0x0, 0x4, 0x1C], memory.read_u16)

    def trickable_timer(self):
        """u16: frames on a trickable surface (ramp). >0 means trick is possible."""
        return self._kart([0x20, "P", 0x0, 0x4, 0xA6], memory.read_u16)

    # =====================================================================
    # KartCollide
    # =====================================================================

    def surface_flags(self):
        """u32: surface type bitfield. 0x1000=on-road, 0x1060/0x1061=off-road."""
        return self._kart([0x20, "P", 0x0, 0x18, 0x18, 0x2C], memory.read_u32)

    def is_offroad(self):
        """Bool: True if currently on off-road surface."""
        return (self.surface_flags() & (1 << 6)) != 0

    def floor_collision_count(self):
        """u16: number of floor collisions. 2=grounded, 1=partial, 0=airborne."""
        return self._kart([0x20, "P", 0x0, 0x18, 0x40], memory.read_u16)

    def race_position(self):
        """u8: current race position (1=first, 2=second, etc)."""
        return self._kart([0x20, "P", 0x0, 0x18, 0x3C], memory.read_u8)

    def respawn_timer(self):
        """u16: Lakitu respawn countdown. 0 = not respawning."""
        return self._kart([0x20, "P", 0x0, 0x18, 0x18, 0x48], memory.read_u16)

    def wall_collide(self):
        """u32: wall collision flags. 0=none, 0x2=wall hit, 0x2002=heavy hit."""
        return self._kart([0x20, "P", 0x0, 0x8, 0x90, 0x8, 0x8], memory.read_u32)

    # =====================================================================
    # Trick
    # =====================================================================

    def trick_cooldown(self):
        """u16: frames until trick can be performed again."""
        return self._kart([0x20, "P", 0x0, 0x28, 0x258, 0x38], memory.read_u16)

    def hop_pos(self):
        """Float: hop height during drift initiation."""
        return self._kart([0x20, "P", 0x44, 0x22C], memory.read_f32)

    # =====================================================================
    # Items (shared / not per-player in this pointer), not implemented as no Item mode is set for training
    # =====================================================================

    def mushroom_count(self):
        """u32: number of mushrooms in inventory."""
        addr = _resolve(_ITEM_HOLDER, [0x14, 0x90])
        return memory.read_u32(addr)

    # =====================================================================
    # Convenience: snapshot all values
    # =====================================================================

    def snapshot(self):
        """Return a dict of all readable values. Useful for logging/debugging."""
        return {
            "race_completion": self.race_completion(),
            "speed": self.speed(),
            "soft_speed_limit": self.soft_speed_limit(),
            "offroad_invincibility": self.offroad_invincibility(),
            "mush_and_boost": self.mush_and_boost(),
            "is_offroad": self.is_offroad(),
            "respawn_timer": self.respawn_timer(),
            "wall_collide": self.wall_collide(),
        }
    
    def snapshotfull(self):
        """Return a dict of all readable values. Useful for logging/debugging."""
        return {
            "stage": self.stage(),
            "race_completion": self.race_completion(),
            "current_lap": self.current_lap(),
            "countdown_timer": self.countdown_timer(),
            "speed": self.speed(),
            "acceleration": self.acceleration(),
            "soft_speed_limit": self.soft_speed_limit(),
            "offroad_invincibility": self.offroad_invincibility(),
            "wheelie_frames": self.wheelie_frames(),
            "wheelie_cooldown": self.wheelie_cooldown(),
            "lean_rot": self.lean_rot(),
            "miniturbo_charge": self.miniturbo_charge(),
            "mt_boost_timer": self.mt_boost_timer(),
            "allmt": self.allmt(),
            "mush_and_boost": self.mush_and_boost(),
            "position": self.position(),
            "bitfield2": self.bitfield2(),
            "airtime": self.airtime(),
            "trickable_timer": self.trickable_timer(),
            "surface_flags": self.surface_flags(),
            "is_offroad": self.is_offroad(),
            "floor_collision_count": self.floor_collision_count(),
            "race_position": self.race_position(),
            "respawn_timer": self.respawn_timer(),
            "wall_collide": self.wall_collide(),
            "trick_cooldown": self.trick_cooldown(),
            "hop_pos": self.hop_pos(),
        }


# ---------------------------------------------------------------------------
# Shared race state (not per-player)
# ---------------------------------------------------------------------------

def read_stage():
    """u32: 1=countdown, 2=racing, 4=finished. Shared across all players."""
    addr = _resolve(_RACE_MANAGER, [0x28])
    return memory.read_u32(addr)
