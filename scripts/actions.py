"""
Action space for Mario Kart Wii RL agent.

Defines a discrete set of meaningful controller input combinations
for a GameCube controller. Each action index maps to a specific
combination of buttons and stick positions.

Controller mapping (MKWii with GC pad):
    A           = Accelerate
    B           = Brake
    R (bool)    = Hop / Drift
    L (bool)    = Use Item
    D-pad Up    = Wheelie (bikes) / Trick (ramps)
    StickX      = Steering (-1.0 = full left, 0.0 = center, 1.0 = full right)

Design decisions:
    - Normal steering: 3 levels (left, center, right)
    - Drift steering:  5 levels (hard left, soft left, center, soft right, hard right)
    - Wheelie/trick always included (wheelie on bikes, trick on ramps for all vehicles)
    - Item actions included for future use (currently items disabled)
    - Every action is a full input snapshot (no partial overrides)

Usage inside a Dolphin script:
    from dolphin import controller, event
    from action_space import ActionSpace

    actions = ActionSpace()

    while True:
        await event.frameadvance()
        action_index = agent.choose_action(observation)
        actions.apply(action_index, controller_id=0)
"""

from dolphin import controller


# ---------------------------------------------------------------------------
# Steering constants
# ---------------------------------------------------------------------------
STEER_LEFT       = -1.0
STEER_SOFT_LEFT  = -0.5
STEER_CENTER     =  0.0
STEER_SOFT_RIGHT =  0.5
STEER_RIGHT      =  1.0


# ---------------------------------------------------------------------------
# Action definition
# ---------------------------------------------------------------------------
class Action:
    """A single discrete action = a full GC controller input snapshot."""
    def __init__(self, name, a_button=False, b_button=False, r_button=False,
                 l_button=False, d_up=False, stick_x=STEER_CENTER):
        self.name = name
        self.a_button = a_button
        self.b_button = b_button
        self.r_button = r_button
        self.l_button = l_button
        self.d_up = d_up
        self.stick_x = stick_x
        
    def to_gc_inputs(self) -> dict:
        """Convert to a GCInputs dict for controller.set_gc_buttons()."""
        return {
            "A": self.a_button,
            "B": self.b_button,
            "R": self.r_button,
            "L": self.l_button,
            "Up": self.d_up,
            # Explicitly release everything else to avoid ghost inputs
            "Down": False,
            "Left": False,
            "Right": False,
            "X": False,
            "Y": False,
            "Z": False,
            "Start": False,
            "StickX": self.stick_x,
            "StickY": 0.0,
            "CStickX": 0.0,
            "CStickY": 0.0,
            "TriggerLeft": 0.0,
            "TriggerRight": 0.0,
        }


# ---------------------------------------------------------------------------
# Action table
# ---------------------------------------------------------------------------
# fmt: off
ACTION_TABLE: list[Action] = [
    # ── Accelerate + Steer (3 levels) ────────────────────────────────────
    Action("accel_center",       a_button=True,  stick_x=STEER_CENTER),     # 0
    Action("accel_left",         a_button=True,  stick_x=STEER_LEFT),       # 1
    Action("accel_right",        a_button=True,  stick_x=STEER_RIGHT),      # 2

    # ── Drift + Steer (5 levels) ─────────────────────────────────────────
    Action("drift_hard_left",    a_button=True,  r_button=True, stick_x=STEER_LEFT),       # 3
    Action("drift_soft_left",    a_button=True,  r_button=True, stick_x=STEER_SOFT_LEFT),   # 4
    Action("drift_center",       a_button=True,  r_button=True, stick_x=STEER_CENTER),      # 5
    Action("drift_soft_right",   a_button=True,  r_button=True, stick_x=STEER_SOFT_RIGHT),  # 6
    Action("drift_hard_right",   a_button=True,  r_button=True, stick_x=STEER_RIGHT),       # 7

    # ── Wheelie/Trick + Steer (3 levels) ─────────────────────────────────
    Action("wheelie_center",     a_button=True,  d_up=True, stick_x=STEER_CENTER),   # 8
    Action("wheelie_left",       a_button=True,  d_up=True, stick_x=STEER_LEFT),     # 9
    Action("wheelie_right",      a_button=True,  d_up=True, stick_x=STEER_RIGHT),    # 10

    # ── Brake + Steer (3 levels) ─────────────────────────────────────────
    Action("brake_center",       b_button=True,  stick_x=STEER_CENTER),     # 11
    Action("brake_left",         b_button=True,  stick_x=STEER_LEFT),       # 12
    Action("brake_right",        b_button=True,  stick_x=STEER_RIGHT),      # 13

    # ── Use Item + Accel + Steer (3 levels) ──────────────────────────────
    Action("item_center",        a_button=True,  l_button=True, stick_x=STEER_CENTER),  # 14
    Action("item_left",          a_button=True,  l_button=True, stick_x=STEER_LEFT),    # 15
    Action("item_right",         a_button=True,  l_button=True, stick_x=STEER_RIGHT),   # 16

    # ── No input (coast) ─────────────────────────────────────────────────
    Action("nothing"),                                                       # 17
]
# fmt: on

NUM_ACTIONS = len(ACTION_TABLE)


# ---------------------------------------------------------------------------
# ActionSpace class
# ---------------------------------------------------------------------------
class ActionSpace:
    """
    Discrete action space for the MKWii RL agent.

    Each integer action index [0, NUM_ACTIONS) maps to a fixed combination
    of GC controller inputs. Call ``apply()`` once per decision step to
    send the chosen action to the emulator.

    Attributes:
        n:          Total number of discrete actions.
        actions:    The full action table (list of Action dataclasses).
    """

    def __init__(self, use_items: bool = True):
        """
        Args:
            use_items: If False, item actions are excluded from the space.
        """
        self.actions: list[Action] = []
        for action in ACTION_TABLE:
            if not use_items and action.l_button:
                continue
            self.actions.append(action)

        self.n: int = len(self.actions)

        # Build name → index lookup
        self._name_to_idx: dict[str, int] = {
            a.name: i for i, a in enumerate(self.actions)
        }

    def apply(self, action_index: int, controller_id: int = 0) -> None:
        """
        Send the given action to the emulator for the current frame.

        Args:
            action_index:  Integer in [0, self.n).
            controller_id: GC controller port (0-based). Default 0.
        """
        gc_inputs = self.actions[action_index].to_gc_inputs()
        controller.set_gc_buttons(controller_id, gc_inputs)

    def get_action_name(self, action_index: int) -> str:
        """Return the human-readable name for an action index."""
        return self.actions[action_index].name

    def get_action_index(self, name: str) -> int:
        """Return the index for a named action."""
        return self._name_to_idx[name]

    def get_gc_inputs(self, action_index: int) -> dict:
        """Return the raw GCInputs dict for an action (useful for debugging)."""
        return self.actions[action_index].to_gc_inputs()

    def describe(self) -> str:
        """Return a formatted table of all actions in the current space."""
        lines = [f"ActionSpace ({self.n} actions):"]
        lines.append(f"{'Idx':>4}  {'Name':<22} {'A':>1} {'B':>1} {'R':>1} {'L':>1} {'Up':>2} {'StickX':>7}")
        lines.append("-" * 52)
        for i, a in enumerate(self.actions):
            lines.append(
                f"{i:>4}  {a.name:<22} "
                f"{'■' if a.a_button else '·'} "
                f"{'■' if a.b_button else '·'} "
                f"{'■' if a.r_button else '·'} "
                f"{'■' if a.l_button else '·'} "
                f"{'■' if a.d_up else ' ·'} "
                f"{a.stick_x:>+5.1f}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ActionSpace(n={self.n})"