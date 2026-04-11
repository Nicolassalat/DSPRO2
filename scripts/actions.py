# actions.py
"""
MKWii RL action space mapping.

Maps our discrete agent actions to actual GameCube controller inputs. 
Decided to stick to a smaller discrete space (18 actions) to make training faster.
Currently items are disabled by default.
"""

from dolphin import controller

# Steering values for StickX
STEER_LEFT       = -1.0
STEER_SOFT_LEFT  = -0.5
STEER_CENTER     =  0.0
STEER_SOFT_RIGHT =  0.5
STEER_RIGHT      =  1.0


class Action:
    # Represents a single frame of GC controller input
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
        # Convert to the dict format Dolphin expects
        return {
            "A": self.a_button,
            "B": self.b_button,
            "R": self.r_button,
            "L": self.l_button,
            "Up": self.d_up,
            
            # TODO: explicitly releasing everything else here because 
            # Dolphin was getting weird ghost inputs otherwise
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


# fmt: off
# black formatting messes up this table, keeping it manual
ACTION_TABLE: list[Action] = [
    # Accel + Steer
    Action("accel_center",       a_button=True,  stick_x=STEER_CENTER),     # 0
    Action("accel_left",         a_button=True,  stick_x=STEER_LEFT),       # 1
    Action("accel_right",        a_button=True,  stick_x=STEER_RIGHT),      # 2

    # Drift + Steer
    Action("drift_hard_left",    a_button=True,  r_button=True, stick_x=STEER_LEFT),       # 3
    Action("drift_soft_left",    a_button=True,  r_button=True, stick_x=STEER_SOFT_LEFT),  # 4
    Action("drift_center",       a_button=True,  r_button=True, stick_x=STEER_CENTER),     # 5
    Action("drift_soft_right",   a_button=True,  r_button=True, stick_x=STEER_SOFT_RIGHT), # 6
    Action("drift_hard_right",   a_button=True,  r_button=True, stick_x=STEER_RIGHT),      # 7

    # Wheelie/Trick + Steer (d_up handles both wheelies for bikes and tricks for ramps)
    Action("wheelie_center",     a_button=True,  d_up=True, stick_x=STEER_CENTER),   # 8
    Action("wheelie_left",       a_button=True,  d_up=True, stick_x=STEER_LEFT),     # 9
    Action("wheelie_right",      a_button=True,  d_up=True, stick_x=STEER_RIGHT),    # 10

    # Brake + Steer
    Action("brake_center",       b_button=True,  stick_x=STEER_CENTER),     # 11
    Action("brake_left",         b_button=True,  stick_x=STEER_LEFT),       # 12
    Action("brake_right",        b_button=True,  stick_x=STEER_RIGHT),      # 13


    # ── Use Item + Accel + Steer (3 levels) ──────────────────────────────
    #Action("item_center",        a_button=True,  l_button=True, stick_x=STEER_CENTER),  # 14
    #Action("item_left",          a_button=True,  l_button=True, stick_x=STEER_LEFT),    # 15
    #Action("item_right",         a_button=True,  l_button=True, stick_x=STEER_RIGHT),   # 16


    # Do nothing
    Action("nothing"),                                                                  # 17
]
# fmt: on

NUM_ACTIONS = len(ACTION_TABLE)


class ActionSpace:
    """
    Wrapper for the discrete action space so the agent can just output an int.
    """

    def __init__(self, use_items: bool = True):
        self.actions: list[Action] = []
        
        # filter out item actions if we don't want them
        for action in ACTION_TABLE:
            if not use_items and action.l_button:
                continue
            self.actions.append(action)

        self.n: int = len(self.actions)

        # Quick lookup dict
        self._name_to_idx: dict[str, int] = {
            a.name: i for i, a in enumerate(self.actions)
        }

    def apply(self, action_index: int, controller_id: int = 0) -> None:
        """Sends the chosen action index to the emulator."""
        gc_inputs = self.actions[action_index].to_gc_inputs()
        controller.set_gc_buttons(controller_id, gc_inputs)

    def get_action_name(self, action_index: int) -> str:
        return self.actions[action_index].name

    def get_action_index(self, name: str) -> int:
        return self._name_to_idx[name]

    def get_gc_inputs(self, action_index: int) -> dict:
        return self.actions[action_index].to_gc_inputs()

    def describe(self) -> str:
        # Prints a nice table of the active action space
        lines = [f"ActionSpace ({self.n} actions):"]
        lines.append(f"{'Idx':>4}  {'Name':<22} {'A':>1} {'B':>1} {'R':>1} {'L':>1} {'Up':>2} {'StickX':>7}")
        lines.append("-" * 52)
        for i, a in enumerate(self.actions):
            lines.append(
                f"{i:>4}  {a.name:<22} "
                f"{'X' if a.a_button else '.'} "
                f"{'X' if a.b_button else '.'} "
                f"{'X' if a.r_button else '.'} "
                f"{'X' if a.l_button else '.'} "
                f"{'X' if a.d_up else ' .'} "
                f"{a.stick_x:>+5.1f}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ActionSpace(n={self.n})"