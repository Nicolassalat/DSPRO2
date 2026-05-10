import os
import random
import threading
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter

import copy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "BTR"))
from networks.btr import BTRNetwork

FRAME_WIDTH = 140
FRAME_HEIGHT = 114
NUM_ACTIONS = 14


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
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
        replay_capacity: int = 100000,
        batch_size: int = 32,
        gamma: float = 0.99,
        lr: float = 1e-4,
        model_path: str | None = None,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_actions = num_actions
        # Use BTRNetwork as the policy network
        input_channels = 1  # Grayscale frames
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
        self.writer = SummaryWriter(log_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "runs"))
        self.load_model()
        self.episode_count = 0

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

    def save_model(self):
        checkpoint = {
            "policy_net": self.policy_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "steps_done": self.steps_done,
        }
        torch.save(checkpoint, self.model_path)

    def _frame_to_tensor(self, frame) -> torch.Tensor:
        if frame.mode != "L":
            frame = frame.convert("L")
        data = torch.from_numpy(np.array(frame, dtype=np.float32))
        return data.unsqueeze(0)

    def select_action(self, frame) -> int:
        if frame is None:
            return random.randrange(self.num_actions)

        state = self._frame_to_tensor(frame).to(self.device)
        self.steps_done += 1

        with torch.no_grad():
            q_values, _ = self.policy_net(state.unsqueeze(0))
            q_mean = q_values.mean(dim=1)  # Average over taus
            return int(q_mean.argmax(dim=1).item())

    def step(self, player_id: int, frame, reward: float, terminal: bool = False) -> int | None:
        if frame is None:
            if terminal:
                self._cleanup_episode(player_id)
            return random.randrange(self.num_actions)

        state = self._frame_to_tensor(frame).to(self.device)
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
            if self.steps_done % 16 == 0:
                self.optimize_model()
            return action

    def _cleanup_episode(self, player_id: int):
        self.last_state[player_id] = None
        self.last_action[player_id] = None

    def optimize_model(self):
        if len(self.replay_buffer) < self.batch_size:
            return

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)
        state_batch = torch.stack(states).to(self.device)
        action_batch = torch.tensor(actions, dtype=torch.int64, device=self.device).unsqueeze(1)
        reward_batch = torch.tensor(rewards, dtype=torch.float32, device=self.device).unsqueeze(1)
        done_batch = torch.tensor(dones, dtype=torch.float32, device=self.device).unsqueeze(1)

        next_state_batch = torch.stack(next_states).to(self.device)

        # current quantile Q-values: (B, n_taus)
        self.policy_net.reset_noise()
        current_q_values, taus = self.policy_net(state_batch)
        current_q = current_q_values.gather(
            2, action_batch.unsqueeze(1).expand(-1, current_q_values.shape[1], -1)
        ).squeeze(2)  # (B, n_taus)

        # target quantile Q-values: (B, n_taus_target) — Double DQN
        self.target_net.reset_noise()
        with torch.no_grad():
            policy_next_q, _ = self.policy_net(next_state_batch)
            best_actions = policy_next_q.mean(dim=1).argmax(dim=1, keepdim=True)
            next_q_values_batch, _ = self.target_net(next_state_batch)
            next_q = next_q_values_batch.gather(
                2, best_actions.unsqueeze(1).expand(-1, next_q_values_batch.shape[1], -1)
            ).squeeze(2)  # (B, n_taus_target)
            target_q = (reward_batch + self.gamma * next_q * (1.0 - done_batch)).detach()

        # quantile Huber loss
        td_errors = target_q.unsqueeze(1) - current_q.unsqueeze(2)  # (B, n_taus, n_taus_target)
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
            self.save_model()

    def close(self):
        self.writer.close()