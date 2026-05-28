# Mario Kart Wii — Reinforcement Learning Agent

## Abstract

Our work aims to design and evaluate a reinforcement learning agent capable of autonomously driving a kart in Mario Kart Wii. The objective is to investigate whether a reinforcement learning agent can learn competitive racing strategies in a dynamic and stochastic environment using only images as input, the same information available to a human player. The agent is trained in split screen mode across four distinct tracks against the game's built-in CPU opponents on hard difficulty, requiring it to adapt its behavior to different track layouts and race situations. Items are disabled to focus the project on core driving skill. During each race the agent must make sequential decisions involving steering, acceleration, drifting, and positioning while responding to unpredictable in-game events like collisions. Because of these stochastic elements, the racing environment provides a challenging setting for studying how reinforcement learning agents develop strategies under uncertainty. By framing Mario Kart Wii as a reinforcement learning environment, this work explores the intersection between autonomous driving and game-playing AI, evaluating how effectively learned policies generalize across different tracks and racing scenarios.

---

## System Requirements

- **OS:** Windows only — the emulator fork has not yet been compiled for Linux, and the screen capture pipeline relies on the Windows-specific `windows-capture` and `pywin32` APIs
- **GPU:** CUDA-capable NVIDIA GPU required — CPU training is not feasible
- **CUDA:** 12.8
- **Python:** 3.12.x
- **RAM:** 32 GB recommended — the replay buffer can grow very large during extended training runs

---

## Architecture

The agent uses a modular deep reinforcement learning architecture defined in `BTR/`:

- **IMPALA Encoder** — convolutional network that compresses raw game frames into a compact feature representation
- **Implicit Quantile Network (IQN)** — distributional RL head that models the full return distribution rather than a single Q-value, improving training stability and sample efficiency
- **NoisyLinear layers** — replace ε-greedy exploration with learnable parametric noise injected directly into network weights, enabling more consistent and state-dependent exploration

---

## Project Structure

```
DSPRO2/
├── BTR/                          Neural network modules (encoder, IQN, layers)
├── scripts/
│   ├── TrainingMonitor_1.ipynb   Entry point — starts training and live reward monitoring
│   ├── StartTraining.py          Training loop (launched by the notebook)
│   ├── TrainingProcess.py        Main training orchestrator
│   ├── neural_agent.py           RL agent implementation
│   ├── DolphinEnv.py             Dolphin emulator environment wrapper
│   ├── DolphinCapture.py         Frame capture from the emulator
│   ├── RewardFunction.py         Reward shaping logic
│   ├── game_memory.py            Game state memory abstraction
│   ├── actions.py                Action space definition
│   ├── open_dolphin.py           Emulator launcher
│   └── setup_emulator.py         First-time emulator setup
├── save_states/                  Emulator save states per track (used during training)
├── save_states_testing/          Emulator save states for evaluation
├── runs_backup/                  Archived training runs (weights, TensorBoard logs, notes)
├── game/                         Place your ROM here as game/mkw.iso
└── assets/                       Game data files
```

---

## Setup

### Prerequisites

- Git
- A Mario Kart Wii ROM file **(PAL region only)** — obtain this independently and place it at `game/mkw.iso`
- A CUDA 12.8 compatible NVIDIA GPU

### Step 1 — Clone the repository

```bash
git clone https://github.com/Nicolassalat/DSPRO2/
cd DSPRO2
```

### Step 2 — Install dependencies

**Option A: uv (recommended)**

Install uv from https://docs.astral.sh/uv/#installation, then run:

```bash
uv sync
```

**Option B: pip**

```bash
pip install -r requirements.txt
```

### Step 3 — Place your ROM

Place your Mario Kart Wii ROM at:

```
game/mkw.iso
```

### Step 4 — Set up the emulator

```bash
# uv
uv run scripts/setup_emulator.py

# pip
python scripts/setup_emulator.py
```

### Step 5 — Activate the environment (pip only)

If you installed via pip, activate the virtual environment before running anything:

- **Windows (cmd):** `.venv\Scripts\activate.bat`

---

## Running Training

Open `scripts/TrainingMonitor_1.ipynb` in Jupyter and run the cells. The notebook:

1. Starts TensorBoard in the background — accessible at [http://localhost:6006](http://localhost:6006)
2. Detects your GPU and warns if none is found
3. Launches the training process and streams a live episode reward plot as training progresses

Stop the active cell to terminate training.

---

## Useful uv Commands

| Command | Description |
|---|---|
| `uv sync` | Sync environment with project dependencies |
| `uv run <command>` | Run a command in the project environment without activating it |
| `uv add <package>` | Add a dependency to the project |
| `uv remove <package>` | Remove a dependency from the project |
| `uv lock` | Update the lock file without installing anything |
| `uv tree` | Show the dependency tree |
| `uv python install <version>` | Install a specific Python version |
| `uv python list` | List available/installed Python versions |
