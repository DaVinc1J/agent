"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script includes a vibe-coded agent controller for human use.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""


import os
import argparse

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from agent import Agent
from definitions import ACTIONS


class HumanAgent(Agent):
    """Human-controlled Wumpus agent.

    The human agent polls pygame keyboard state for Wumpus actions.
    update() stores the latest percept dictionary keyed by sense name.
    """

    def reset(self):
        """Clear queued input and remembered key state for a new cave."""
        super().reset()
        self.pending_action = None
        self.previous_keys = set()

    def queue_action(self, action):
        """Store a valid human-selected action until act() is called."""
        if action not in ACTIONS:
            return
        self.pending_action = action

    def handle_key(self, key):
        """Compatibility helper for tests or non-pygame wrappers."""
        keymap = {
            pygame.K_SPACE: "FORWARD",
            pygame.K_LEFT: "LEFT",
            pygame.K_RIGHT: "RIGHT",
            pygame.K_z: "SHOOT",
            pygame.K_x: "GRAB",
            pygame.K_q: "EXIT",
        }
        action = keymap.get(key)
        if action is None:
            return False
        self.queue_action(action)
        return True

    def act(self):
        """Poll keyboard input and return one human action, or None."""
        action = self.pending_action or self._pressed_action()
        self.pending_action = None
        return self.remember_action(action)

    def _pressed_action(self):
        """Return the first newly pressed game key as an action."""
        keys = pygame.key.get_pressed()
        keymap = [
            (pygame.K_SPACE, "FORWARD"),
            (pygame.K_LEFT, "LEFT"),
            (pygame.K_RIGHT, "RIGHT"),
            (pygame.K_z, "SHOOT"),
            (pygame.K_x, "GRAB"),
            (pygame.K_q, "EXIT"),
        ]
        pressed = {key for key, action in keymap if keys[key]}
        new_presses = pressed - self.previous_keys
        self.previous_keys = pressed

        for key, action in keymap:
            if key in new_presses:
                return action
        return "NO_ACTION"


def parse_args():
    """Read command-line options for launching the human-controlled emulator."""
    parser = argparse.ArgumentParser(description="Run Wumpus World with the human agent.")
    parser.add_argument("--config", default="game_config.yaml", help="YAML config file for game parameters.")
    parser.add_argument("--cave", default="default", help="Named cave profile from the YAML config.")
    parser.add_argument("--show-window", choices=("true", "false"), help="Override emulator.show_window from the config.")
    parser.add_argument("--seed", help="Override cave.seed from the config with an integer.")
    return parser.parse_args()


def main():
    """Create a HumanAgent and launch the pygame emulator."""
    args = parse_args()

    from console import PygameApp
    from utils import load_config

    agent = HumanAgent()
    # The human-controlled agent requires a visible pygame window for keyboard input.
    show_window = args.show_window if args.show_window is not None else "true"
    config = load_config(args.config, cave_name=args.cave, show_window=show_window, seed=args.seed)
    PygameApp(agent=agent, config=config).run()


if __name__ == "__main__":
    main()
