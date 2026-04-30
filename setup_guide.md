# Mario Kart Wii Reinforcement Learning — Setup Guide

## Step 1: Clone the Git Repository
```
git clone https://github.com/Nicolassalat/DSPRO2/
```
## Step 2: Download UV
Download and install UV from: https://docs.astral.sh/uv/#installation

## Step 3: Download Mario Kart Wii ROM
Download the ROM from: https://romsretro.com/mario-kart-wii-rom/ (but pssst... not quite legal 🤫)
place at game/mkw.iso

## Step 4: Navigate into the Project Folder
```
cd DSPRO2
```

## Step 5: Create the Virtual Environment and Install Dependencies
```
uv init
uv sync
uv lock
```

## Step 6: Activate the Environment
- **macOS/Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
---

## Step 7: Download Emulator setup (only windows for now)
```
uv run scripts/setup_emulator.py
```

The emulator fork is not yet compiled for linux and must be built from source.

## Useful UV Commands
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

