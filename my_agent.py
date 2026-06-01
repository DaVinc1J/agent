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

@dataclass
class dir:
    north = (0, 1)
    east = (1, 0)
    south = (0, -1)
    west = (-1, 0)

@dataclass
class sense:
    stench = "Stench"
    breeze = "Breeze"
    glimmer = "Glimmer"
    bump = "bump"
    screem = "scream"

@dataclass
class state:
    find_width = -1
    explore = 0
    analyse = 1
    exit = 2

class MyAgent(Agent):

    def __init__(self):
        super(MyAgent, self).__init__()
        self.state = None
        self.actions = None
        self.board = np.zeros((4,4), dtype=int)
        self.location = (0,0)
        self.direction = dir.east
        self.breezes = []
        self.stenches = []
        self.prev_positions = [self.location]

    def reset(self):
        """Reset all state before a new cave starts."""
        super(MyAgent, self).reset()
        self.state = state.find_width
        self.actions = list()
        self.board = np.zeros((4,4), dtype=int)

    def get_action(self, direction):
        action = []

        if direction == dir.north:
            action.append('UP')
        elif direction == dir.south:
            action.append('DOWN')
        elif direction == dir.east:
            action.append('RIGHT')
        elif direction == dir.west:
            action.append('LEFT')

        return action

    def locate_wumpus(self):
        last_pos = self.prev_positions.last()
        go_back = (
            last_pos[0] - self.location[0],
            last_pos[1] - self.location[1]
        )
        
        actions = []
        actions.append(self.get_action(go_back))

        go_around = {(
            go_back[1] * -1,
            go_back[0] * 0,
        ), (
            go_back[0] * -1,
            go_back[1] * -1,
        )}

        actions.append(self.get_action(go_around[0]))
        actions.append(self.get_action(go_around[1]))

    def act(self):
        print('Current State is: {}'.format(self.state))



        if self.state == 'EXPLORE':
            if self.last_senses[sense.glimmer]:
                actions = ['GRAB']
                self.state = 'GO_TO_ORIGIN'
            else:
                if self.location[0] + self.direction[0] > 4:
                    if self.location[1] == 1:
                        actions = ['RIGHT']
                    elif self.location[1] == 4:
                        actions = ['LEFT']
                    else:
                        actions = ['LEFT', 'RIGHT']

                else:
                    actions = ["FORWARD"]
        elif self.state == 'GO_TO_ORIGIN':
            if self.location == (1,1):
                actions = ['EXIT']
            else:
                if self.direction[0] != -1 and self.direction[1] != -1:
                    actions = ['LEFT', 'RIGHT']
                else:
                    if self.location[0] + self.direction[0] > 4 or self.location[0] + self.direction[0] < 1 or self.location[1] + self.direction[1] > 4 or self.location[1] + self.direction[1] < 1:
                        actions = ['LEFT', 'RIGHT']
                    else:
                        actions = ["FORWARD"]
                


        """
        if self.state == 'EXPLORE':
           if self.last_action == 'FORWARD':
                if self.last_senses['Bump']:
                    actions = ['LEFT', 'RIGHT']
                elif self.last_senses['Glimmer']:
                    actions = ['GRAB']
                else:
                    actions = ['FORWARD', 'LEFT', 'RIGHT']
            else:
                actions = ['FORWARD', 'LEFT', 'RIGHT']
        else:
            if self.last_action == 'FORWARD':
                if self.last_senses['Bump']:
                    actions = ['LEFT', 'RIGHT']
                else:
                    # a new place
                    actions = ['EXIT']
            elif self.last_action == 'EXIT':
                actions = ['FORWARD', 'LEFT', 'RIGHT']
            else:
                actions = ['FORWARD', 'LEFT', 'RIGHT']
        """

        action =  np.random.choice(actions)

        self.remember_action(action)
        print("Current action: {}".format(action))
        return action

    def update(self, senses):
        super(MyAgent, self).update(senses)
        print(" senses: {}".format(senses))

        self.location = (self.location[0] + self.direction[0], self.location[1] + self.direction[1])
        if self.last_action == 'LEFT' or self.last_action == 'RIGHT':
            if self.last_action == 'LEFT':
                self.direction = (-self.direction[1], self.direction[0])
            else:
                self.direction = (self.direction[1], -self.direction[0])

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
