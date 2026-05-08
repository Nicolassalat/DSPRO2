# RewardFunction.py

# Set to True when training with items (mushrooms grant offroad invincibility)
USE_ITEMS = False


def compute_reward(snapshot: dict, progress_delta: float, done: bool, stuck: bool) -> float:

    if done:
        return +10.0
    if stuck:
        return -5.0

    reward = 0.0

    # Core signal: progress scaled by speed
    speed_ratio = snapshot["speed"] / snapshot["soft_speed_limit"] if snapshot["soft_speed_limit"] > 0 else 0.0
    reward += progress_delta * 100.0 * (1.0 + speed_ratio)

    # Speed penalty — discourages standing still
    if snapshot["speed"] < 10.0:
        reward -= 0.1

    # Boost panel bonus — rewards hitting boost panels instead of driving around them
    if snapshot["mush_and_boost"] > 0:
        reward += 0.2

    # Off-road penalty
    if USE_ITEMS:
        # With items: only penalise offroad when not mushroom-boosted
        if snapshot["is_offroad"] and snapshot["offroad_invincibility"] == 0:
            reward -= 0.3
    else:
        # Without items: always penalise offroad
        if snapshot["is_offroad"]:
            reward -= 0.3

    # Respawn penalty (falling off track / Lakitu)
    if snapshot["respawn_timer"] > 0:
        reward -= 0.5

    # Wall collision penalty
    if snapshot["wall_collide"] > 0:
        reward -= 0.2

    return reward