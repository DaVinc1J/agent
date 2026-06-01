"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script shows an example agent that makes random actions.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

import argparse
import numpy as np
from agent import Agent
from dataclasses import dataclass

import pathfinder

VECTORS = {
    "North": (1, 0),
    "East": (0, 1),
    "South": (-1, 0),
    "West": (0, -1),
}

@dataclass
class dir:
    north = (1, 0)
    east = (0, 1)
    south = (-1, 0)
    west = (0, -1)

from enum import Enum

class Action(Enum):
    FOUND_WIDTH = 'FOUND_WIDTH'
    FORWARD = 'FORWARD'
    TURN_LEFT = 'TURN_LEFT'
    TURN_RIGHT = 'TURN_RIGHT'

class MyAgent(Agent):

    START = (1, 1)

    def __init__(self):
        super(MyAgent, self).__init__()
        self.state = None
        self.actions = None
        self.board = np.zeros((4,4), dtype=int)
        self.location = self.START
        self.direction = dir.east
        self.breezes = []
        self.stenches = []
        self.width = None
        self.height = None
        self._width_steps = 0
        self._height_steps = 0
        self.visited_senses = {}

    def reset(self):
        """Reset all state before a new cave starts."""
        super(MyAgent, self).reset()
        self.state = 'FIND_WIDTH'
        self.actions = list()
        self.board = np.zeros((4,4), dtype=int)
        self.location = self.START
        self.direction = dir.east
        self.width = None
        self.height = None
        self._width_steps = 0
        self._height_steps = 0
        self.visited_senses = {}

    def _turn_toward(self, target):
        """Return 'LEFT' or 'RIGHT' to rotate one step toward target direction,
        or None if already facing it. Matches the game's DIRECTIONS rotation
        (console.py:135) where LEFT from E goes to N."""
        if self.direction == target:
            return None
        right = (-self.direction[1], self.direction[0])
        return 'RIGHT' if right == target else 'LEFT'

    # Cave profiles cap width/height at 6 (cave_config.yaml `large`),
    # used as a fallback when sizing aborts on a hazard.
    MAX_DIM = 6

    def find_width(self):
        """Walk east counting successful steps until a Bump sets self.width.
        Aborts (returns None without setting width) if the current cell shows
        Stench or Breeze, since stepping forward could be fatal."""
        if self.width is not None:
            return None
        senses = self.last_senses or {}
        if self.last_action == 'FORWARD' and self.direction == dir.east:
            if senses.get('Bump'):
                self.width = 1 + self._width_steps
                return None
            self._width_steps += 1
        if senses.get('Stench') or senses.get('Breeze'):
            return None
        turn = self._turn_toward(dir.east)
        return turn if turn is not None else 'FORWARD'

    def find_height(self):
        if self.height is not None:
            return None

        senses = self.last_senses
        if self.last_action == 'FORWARD' and self.direction == dir.north:
            if senses.get('Bump'):
                self.height = 1 + self._height_steps
                return None
            self._height_steps += 1
        if senses.get('Stench') or senses.get('Breeze'):
            return None
        turn = self._turn_toward(dir.north)
        return turn if turn is not None else 'FORWARD'

    def _is_safe(self, cell):
        if cell in self.visited_senses:
            return True

        r, c = cell

        cleared_wumpus = False
        cleared_pit = False

        for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            n = (r + dr, c + dc)
            s = self.visited_senses.get(n)

            if s is None:
                continue

            if not s.get('Stench'):
                cleared_wumpus = True
            if not s.get('Breeze'):
                cleared_pit = True

        return cleared_wumpus and cleared_pit

    def _safe_grid(self):
        rows = self.height + 1 # + 1 to be 1-indexed
        cols = self.width + 1 # see above
        grid = np.full((rows, cols), 'X', dtype=object) # assume unsafe
        for r in range(1, rows):
            for c in range(1, cols):
                if self._is_safe((r, c)):
                    grid[r][c] = 1
        return grid

    def _action_for_step(self, next_cell):
        delta = (next_cell[0] - self.location[0], next_cell[1] - self.location[1])
        if delta != self.direction:
            return self._turn_toward(delta)
        return 'FORWARD'

    def _route_action(self, target):
        """Return the next action to step toward target along a safe BFS path,
        or None if no safe route exists."""
        if self.location == target:
            return None
        grid = self._safe_grid()
        path = pathfinder.bfs(
            self.location, target,
            (self.height + 1, self.width + 1), grid,
        )
        if not path:
            return None
        return self._action_for_step(path[0])

    def _next_explore(self):
        """Pick the nearest reachable unvisited safe cell and step toward it."""
        rows = self.height + 1 # + 1 to be 1-indexed
        cols = self.width + 1 # see above
        grid = self._safe_grid()
        path = None
        for r in range(1, rows):
            for c in range(1, cols):
                cell = (r, c)

                if cell == self.location or cell in self.visited_senses or not self._is_safe(cell):
                    continue

                new = pathfinder.bfs(
                    self.location, cell,
                    (rows, cols), grid,
                )
                if new and (path is None or len(new) < len(path)):
                    path = new
        if not path:
            return None
        return self._action_for_step(path[0])

    def _emit(self, action):
        self.remember_action(action)
        print(f"Current action: {action}\n")
        return action

    def act(self):
        print(f"Current State is: {self.state} loc={self.location} dir={self.direction} w={self.width} h={self.height}\n")

        if self.last_senses is None:
            return self._emit('NO_ACTION')

        if self.state == 'FIND_WIDTH':
            action = self.find_width()
            if action is not None:
                return self._emit(action)
            if self.width is None:
                self.width = self.MAX_DIM
            self.state = 'FIND_HEIGHT'

        if self.state == 'FIND_HEIGHT':
            action = self.find_height()
            if action is not None:
                return self._emit(action)
            if self.height is None:
                self.height = self.MAX_DIM
            self.state = 'EXPLORE'

        if self.last_senses.get('Glimmer'):
            self.state = 'GO_TO_ORIGIN'
            return self._emit('GRAB')

        if self.state == 'EXPLORE':
            action = self._next_explore()
            if action is not None:
                return self._emit(action)
            self.state = 'GO_TO_ORIGIN'

        if self.state == 'GO_TO_ORIGIN':
            if self.location == self.START:
                return self._emit('EXIT')
            action = self._route_action(self.START)
            if action is not None:
                return self._emit(action)

        return self._emit('NO_ACTION')

    def update(self, senses):
        super(MyAgent, self).update(senses)
        print(" senses: {}".format(senses))

        # Rotate first, then advance only on a successful FORWARD.
        # LEFT: (dr,dc) -> (dc,-dr) matches console.py:135 (E->N).
        # RIGHT: (dr,dc) -> (-dc,dr) matches console.py:137 (E->S).
        if self.last_action == 'LEFT':
            self.direction = (self.direction[1], -self.direction[0])
        elif self.last_action == 'RIGHT':
            self.direction = (-self.direction[1], self.direction[0])
        elif self.last_action == 'FORWARD' and not senses.get('Bump'):
            self.location = (
                self.location[0] + self.direction[0],
                self.location[1] + self.direction[1],
            )

        self.visited_senses[self.location] = dict(senses)

def parse_args():
    """Read command-line options for launching the logic-agent emulator."""
    parser = argparse.ArgumentParser(description="Run Wumpus World with the logic agent.")
    parser.add_argument("--config", default="game_config.yaml", help="YAML config file for game parameters.")
    parser.add_argument("--cave", default="gold", help="Named cave profile from the YAML config.")
    parser.add_argument("--show-window", default="true", help="Override emulator.show_window from the config.")
    parser.add_argument("--seed", help="Override cave.seed from the config with an integer.")
    return parser.parse_args()


def main():
    """Create a MyAgent and launch the pygame emulator in auto-play mode."""
    args = parse_args()

    from console import PygameApp
    from utils import load_config

    agent = MyAgent()
    config = load_config(args.config, cave_name=args.cave, show_window=args.show_window, seed=args.seed)
    PygameApp(agent=agent, config=config).run()

if __name__ == "__main__":
    main()
