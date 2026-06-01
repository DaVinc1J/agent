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
from enum import Enum
from enum import StrEnum

import pathfinder
from agent import Agent

class action(StrEnum):
    FORWARD = "FORWARD"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    GRAB = "GRAB"
    SHOOT = "SHOOT"
    EXIT = "EXIT"
    NO_ACTION = "NO_ACTION"


class dir():
    N = (1, 0)
    E = (0, 1)
    S = (-1, 0)
    W = (0, -1)

class dim(StrEnum):
    UNKNOWN = "UNKNOWN"

class MyAgent(Agent):

    START = (1, 1)
    MAX_DIM = 6  # cave_config.yaml `large` caps width/height at 6.

    def reset(self):
        """Reset all state before a new cave starts."""
        super().reset()
        self.last_senses = {}
        self.state = 'FIND_WIDTH'
        self.location = self.START
        self.direction = dir.E
        self.width = dim.UNKNOWN
        self.height = dim.UNKNOWN
        self._width_steps = 0
        self._height_steps = 0
        self.visited_senses = {}

    def _turn_or_move_toward(self, target):
        if self.direction == target:
            return action.FORWARD

        right = (-self.direction[1], self.direction[0])

        if right == target:
            return action.RIGHT
        else:
            return action.LEFT

    def find_wall(self, wall_direction, steps):
        if self.last_action == action.FORWARD and self.direction == wall_direction:
            if self.last_senses.get('Bump'):
                return None, steps, True
            steps += 1

        if self.last_senses.get('Stench') or self.last_senses.get('Breeze'):
            return None, steps, False

        turn = self._turn_or_move_toward(wall_direction)
        return turn, steps, False

    def find_width(self):
        if self.width is not dim.UNKNOWN:
            return None

        action, self._width_steps, bumped = self.find_wall(dir.E, self._width_steps)
        if bumped:
            self.width = 1 + self._width_steps

        return action

    def find_height(self):
        if self.height is not dim.UNKNOWN:
            return None
        action, self._height_steps, bumped = self.find_wall(dir.N, self._height_steps)
        if bumped:
            self.height = 1 + self._height_steps
        return action

    def _is_safe(self, cell):
        if cell in self.visited_senses:
            return True

        if self.width is None or self.height is None:
            return False

        r, c = cell

        if not (1 <= r <= self.height and 1 <= c <= self.width):
            return False

        cleared_wumpus = False
        cleared_pit = False

        for dr, dc in (dir.N, dir.E, dir.S, dir.W):
            s = self.visited_senses.get((r + dr, c + dc))
            if s is None:
                continue
            
            if not s.get('Stench'):
                cleared_wumpus = True
            if not s.get('Breeze'):
                cleared_pit = True
        
        is_safe = cleared_wumpus and cleared_pit
        return is_safe

    def _safe_grid(self):
        rows = self.height + 1
        cols = self.width + 1
        grid = np.full((rows, cols), 'X', dtype=object)
        for r in range(1, rows):
            for c in range(1, cols):
                if self._is_safe((r, c)):
                    grid[r][c] = 1
        return grid

    def _step_action_to(self, cell):
        goal_direction = (cell[0] - self.location[0], cell[1] - self.location[1])
        return self._turn_or_move_toward(goal_direction)

    def _bfs(self, target, grid=None):
        if grid is None:
            grid = self._safe_grid()

        return pathfinder.bfs(
            self.location, target,
            (self.height + 1, self.width + 1), grid,
        )

    def _route_action(self, target):
        if self.location == target:
            return None
        path = self._bfs(target)
        return self._step_action_to(path[0]) if path else None

    def _next_explore_action(self):
        rows = self.height + 1
        cols = self.width + 1
        grid = self._safe_grid()
        best = None
        for r in range(1, rows):
            for c in range(1, cols):
                cell = (r, c)

                if cell == self.location or cell in self.visited_senses:
                    continue

                if not self._is_safe(cell):
                    continue

                path = self._bfs(cell, grid)
                if path and (best is None or len(path) < len(best)):
                    best = path

        return self._step_action_to(best[0]) if best else None

    def act(self):
        if self.last_senses is None:
            return self.remember_action(action.NO_ACTION)

        if self.state == 'FIND_WIDTH':
            action = self.find_width()

            if action is not None:
                return self.remember_action(action)

            if self.width is dim.UNKNOWN:
                self.width = 1 + self._width_steps

            self.state = 'FIND_HEIGHT'

        if self.state == 'FIND_HEIGHT':
            action = self.find_height()

            if action is not None:
                return self.remember_action(action)

            if self.height is dim.UNKNOWN:
                self.height = 1 + self._height_steps

            self.state = 'EXPLORE'

        if self.last_senses.get('Glimmer'):
            self.state = 'GO_TO_ORIGIN'
            return self.remember_action(action.GRAB)

        if self.state == 'EXPLORE':
            action = self._next_explore_action()
            if action is not None:
                return self.remember_action(action)
            self.state = 'GO_TO_ORIGIN'

        if self.state == 'GO_TO_ORIGIN':

            if self.location == self.START:
                return self.remember_action(action.EXIT)

            action = self._route_action(self.START)

            if action is not None:
                return self.remember_action(action)

        return self.remember_action(action.NO_ACTION)

    def update(self, senses):
        super().update(senses)
        if self.last_action == action.LEFT:
            self.direction = (self.direction[1], -self.direction[0])
        elif self.last_action == action.RIGHT:
            self.direction = (-self.direction[1], self.direction[0])
        elif self.last_action == action.FORWARD and not senses.get('Bump'):
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
