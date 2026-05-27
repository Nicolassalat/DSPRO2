# neural_agent.py
import os
import random
import shutil
import threading
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter
import pynvml
import pickle

import copy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "BTR"))
from networks.btr import BTRNetwork

FRAME_WIDTH = 140
FRAME_HEIGHT = 114
NUM_ACTIONS = 15
FRAME_STACK = 4


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        # state/next_state stored as uint8 CPU tensors to minimise VRAM
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)


class NeuralAgent:
    def __init__(
        self,
        num_actions: int = NUM_ACTIONS,
        replay_capacity: int = 50000,
        batch_size: int = 32,
        gamma: float = 0.99,
        lr: float = 1e-4,
        model_path: str | None = None,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device.type == "cuda":
            torch.cuda.set_per_process_memory_fraction(0.75)
        self.num_actions = num_actions
        input_channels = FRAME_STACK
        input_shape = (FRAME_HEIGHT, FRAME_WIDTH)
        features_dim = 256
        channel_list = [32, 64, 64]
        n_taus = 8
        embedding_dim = 64
        self.policy_net = BTRNetwork(
            input_channels=input_channels,
            input_shape=input_shape,
            features_dim=features_dim,
            channel_list=channel_list,
            num_actions=num_actions,
            n_taus=n_taus,
            embedding_dim=embedding_dim
        ).to(self.device)
        self.target_net = copy.deepcopy(self.policy_net)
        for p in self.target_net.parameters():
            p.requires_grad = False
        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=lr)
        self.replay_buffer = ReplayBuffer(replay_capacity)
        self.batch_size = batch_size
        self.gamma = gamma
        self.steps_done = 0
        self.lock = threading.Lock()

        self.last_state = {1: None, 2: None}
        self.last_action = {1: None, 2: None}
        self.model_path = model_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent_model.pth")
        self.project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        self.writer = SummaryWriter(log_dir=os.path.join(self.project_root, "runs"))
        self.load_model()
        self.episode_count = 0

        # Determine run number once at startup
        backup_dir = os.path.join(self.project_root, "runs_backup")
        os.makedirs(backup_dir, exist_ok=True)
        existing_nums = []
        for d in os.listdir(backup_dir):
            if d.startswith("run"):
                try:
                    existing_nums.append(int(d[3:]))
                except ValueError:
                    pass
        self.run_num = max(existing_nums, default=0) + 1
        print(f"[NeuralAgent] This run will be backed up as run{self.run_num}")

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.policy_net.load_state_dict(checkpoint.get("policy_net", self.policy_net.state_dict()))
                self.optimizer.load_state_dict(checkpoint.get("optimizer", self.optimizer.state_dict()))
                self.steps_done = checkpoint.get("steps_done", self.steps_done)
                print(f"[NeuralAgent] Loaded model from {self.model_path}")
            except Exception as exc:
                print(f"[NeuralAgent] Failed to load model: {exc}")

        buffer_path = self.model_path.replace(".pth", "_buffer.pkl")
        if os.path.exists(buffer_path):
            try:
                with open(buffer_path, "rb") as f:
                    loaded = pickle.load(f)
                if isinstance(loaded, list):
                    self.replay_buffer.buffer = deque(loaded, maxlen=self.replay_buffer.capacity)
                else:
                    self.replay_buffer.buffer = loaded
                print(f"[NeuralAgent] Loaded replay buffer ({len(self.replay_buffer)} transitions)")
            except Exception as exc:
                print(f"[NeuralAgent] Failed to load replay buffer: {exc}")

    def save_model(self):
        checkpoint = {
            "policy_net": self.policy_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "steps_done": self.steps_done,
        }
        torch.save(checkpoint, self.model_path)

        with self.lock:
            buffer_snapshot = list(self.replay_buffer.buffer)
        
        buffer_path = self.model_path.replace(".pth", "_buffer.pkl")
        tmp_path = buffer_path + ".tmp"
        with open(tmp_path, "wb") as f:
            pickle.dump(buffer_snapshot, f)
        os.replace(tmp_path, buffer_path)

    def save_snapshot(self, track: str):
        threading.Thread(target=self._do_snapshot, args=(track,), daemon=True).start()

    def _do_snapshot(self, track: str):
        self.save_model()
        self.writer.flush()

        run_dir = os.path.join(self.project_root, "runs_backup", f"run{self.run_num}", f"after_{track}")
        os.makedirs(run_dir, exist_ok=True)

        shutil.copy2(self.model_path, os.path.join(run_dir, "agent_model.pth"))
        buffer_path = self.model_path.replace(".pth", "_buffer.pkl")
        if os.path.exists(buffer_path):
            shutil.copy2(buffer_path, os.path.join(run_dir, "agent_model_buffer.pkl"))

        crash_log = os.path.join(self.project_root, "crash_log.txt")
        if os.path.exists(crash_log):
            shutil.copy2(crash_log, os.path.join(run_dir, "crash_log.txt"))

        runs_src = os.path.join(self.project_root, "runs")
        if os.path.exists(runs_src):
            shutil.copytree(runs_src, os.path.join(run_dir, "runs"), dirs_exist_ok=True)

        state_src = os.path.join(self.project_root, "scripts", "training_state.json")
        if os.path.exists(state_src):
            scripts_dst = os.path.join(run_dir, "scripts")
            os.makedirs(scripts_dst, exist_ok=True)
            shutil.copy2(state_src, os.path.join(scripts_dst, "training_state.json"))

        print(f"[NeuralAgent] Snapshot saved to runs_backup/run{self.run_num}/after_{track}/")

    def _frame_to_tensor(self, frame) -> torch.Tensor:
        # Store as uint8 on CPU — saves ~4x VRAM vs float32
        return torch.from_numpy(np.array(frame, dtype=np.uint8))  # [4, H, W], CPU

    def _to_float(self, state_tensor: torch.Tensor) -> torch.Tensor:
        # Convert uint8 CPU → float32 GPU, normalised to [0, 1]
        return state_tensor.to(self.device, dtype=torch.float32) / 255.0

    def select_action(self, frame) -> int:
        if frame is None:
            return random.randrange(self.num_actions)

        self.steps_done += 1

        eps = max(0.0, 1.0 - self.steps_done / 50000)
        if random.random() < eps:
            return random.randrange(self.num_actions)

        state = self._to_float(self._frame_to_tensor(frame))
        with torch.no_grad():
            q_values, _ = self.policy_net(state.unsqueeze(0))
            q_mean = q_values.mean(dim=1)
            return int(q_mean.argmax(dim=1).item())

    def step(self, player_id: int, frame, reward: float, terminal: bool = False) -> int | None:
        if frame is None:
            if terminal:
                self._cleanup_episode(player_id)
            return random.randrange(self.num_actions)

        # Store as uint8 CPU tensor
        state = self._frame_to_tensor(frame)
        with self.lock:
            if self.last_state[player_id] is not None and self.last_action[player_id] is not None:
                self.replay_buffer.push(
                    self.last_state[player_id],
                    self.last_action[player_id],
                    reward,
                    state,
                    terminal,
                )

            if terminal:
                self._cleanup_episode(player_id)
                self.optimize_model()
                return None

            action = self.select_action(frame)
            self.last_state[player_id] = state
            self.last_action[player_id] = action
            if self.steps_done % 64 == 0:
                self.optimize_model()
            return action

    def _cleanup_episode(self, player_id: int):
        self.last_state[player_id] = None
        self.last_action[player_id] = None

    def optimize_model(self):
        if len(self.replay_buffer) < self.batch_size:
            return

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        # Convert uint8 CPU → float32 GPU, normalised to [0, 1]
        state_batch = torch.stack([self._to_float(s) for s in states])
        next_state_batch = torch.stack([self._to_float(s) for s in next_states])

        action_batch = torch.tensor(actions, dtype=torch.int64, device=self.device).unsqueeze(1)
        reward_batch = torch.tensor(rewards, dtype=torch.float32, device=self.device).unsqueeze(1)
        done_batch = torch.tensor(dones, dtype=torch.float32, device=self.device).unsqueeze(1)

        self.policy_net.reset_noise()
        current_q_values, taus = self.policy_net(state_batch)
        current_q = current_q_values.gather(
            2, action_batch.unsqueeze(1).expand(-1, current_q_values.shape[1], -1)
        ).squeeze(2)

        self.target_net.reset_noise()
        with torch.no_grad():
            policy_next_q, _ = self.policy_net(next_state_batch)
            best_actions = policy_next_q.mean(dim=1).argmax(dim=1, keepdim=True)
            next_q_values_batch, _ = self.target_net(next_state_batch)
            next_q = next_q_values_batch.gather(
                2, best_actions.unsqueeze(1).expand(-1, next_q_values_batch.shape[1], -1)
            ).squeeze(2)
            target_q = (reward_batch + self.gamma * next_q * (1.0 - done_batch)).detach()

        td_errors = target_q.unsqueeze(1) - current_q.unsqueeze(2)
        huber = F.huber_loss(current_q.unsqueeze(2).expand_as(td_errors),
                             target_q.unsqueeze(1).expand_as(td_errors),
                             reduction="none", delta=1.0)
        taus_expanded = taus.unsqueeze(2).expand_as(td_errors)
        loss = (torch.abs(taus_expanded - (td_errors < 0).float()) * huber).mean()
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 10.0)
        self.optimizer.step()

        self.writer.add_scalar("train/loss", loss.item(), self.steps_done)
        self.writer.add_scalar("train/mean_q", current_q.mean().item(), self.steps_done)

        if self.steps_done % 1000 == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
            threading.Thread(target=self.save_model, daemon=True).start()
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                self.writer.add_scalar("crash_debug/gpu_temp", temp, self.steps_done)
            except:
                pass

    def close(self):
        self.writer.close()