# RewardFunction.py — simple reward for pretraining
# Goal: teach the agent to drive forward and complete laps.
# Switch to RewardFunction_advanced.py for fine-tuning.

def compute_reward(snapshot: dict, progress_delta: float, done: bool, stuck: bool) -> float:

    return progress_delta * 50
