# Run 5 - Actions for all 4 frames during frame skip

![Run 5 ensorBoard](run5board.png)

## Key Change
Fixed critical bug where controller inputs were only applied on every 4th frame during frameskip. Actions are now held continuously across all 4 frames, giving the agent proper control authority.

## Configuration
- Frame stacking: 4 frames
- Reward: `progress_delta * 50` (simple forward progress only)
- Replay buffer: 20k
- Action space: 15 actions
- Optimize frequency: every 64 steps

## Early Observations
- Agents are visibly driving for the first time
- Previously agents would coast on save state momentum then stop — this is no longer observed
- first full race completion after just 137 episodes with 2 more between episodes 143-173
- Strategy: wall hugging on the outside — valid but suboptimal racing line
- mean_q rising steadily throughout, no divergence
- Progress and reward both trending upward consistently

## Next Steps
- Let run overnight to observe if cleaner racing lines emerge naturally
- If wall hugging persists, switch to advanced reward function with wall collision and offroad penalties to incentivize cleaner driving
- Goal: beat easy CPU difficulty