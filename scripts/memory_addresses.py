# memory_addresses.py
# Mario Kart Wii - NTSC-U (RMCE01)
# Confirmed stable across Dolphin restarts (2 sessions verified)

RACE_DATA_PTR = 0x8016C708          # static pointer to player race struct
                                     # alternatives (same result): 0x8016CA18, 0x8016CD60, 0x8016D494

LAP_COMPLETION_CURRENT_OFFSET = 0x154  # float, decreases when reversing
LAP_COMPLETION_MAX_OFFSET     = 0x158  # float, only ever increases (4.0 = finish)