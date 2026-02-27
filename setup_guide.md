# Mario Kart Wii Reinforcement Learning — Setup Guide

## Step 1: Download UV
Download and install UV from: https://docs.astral.sh/uv/#installation

## Step 2: Download Dolphin Emulator
Download and install Dolphin from: https://de.dolphin-emu.org/

## Step 3: Download Mario Kart Wii ROM
Download the ROM from: https://romsretro.com/mario-kart-wii-rom/ (but pssst... not quite legal 🤫)

## Step 4: Clone the Git Repository
```
git clone <repository-url>
```

## Step 5: Navigate into the Project Folder
```
cd <project-name>
```

## Step 6: Create the Virtual Environment and Install Dependencies
```
uv sync
```

## Step 7: Activate the Environment
- **macOS/Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`

---

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
