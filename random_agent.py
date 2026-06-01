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


class RandomAgent(Agent):

    def __init__(self):
        super(RandomAgent, self).__init__()
        self.state = None
        self.actions = None

    def reset(self):
        """Reset all state before a new cave starts."""
        super(RandomAgent, self).reset()
        self.state = 'EXPLORE'
        self.actions = list()

    def act(self):
        print('Current State is: {}'.format(self.state))

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

        action =  np.random.choice(actions)

        self.remember_action(action)
        print("Current action: {}".format(action))
        return action

    def update(self, senses):
        super(RandomAgent, self).update(senses)
        print(" senses: {}".format(senses))

        if self.last_action == 'GRAB' and senses['Glimmer'] is False:
            self.state = 'GO_TO_ORIGIN'

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

    agent = RandomAgent()
    config = load_config(args.config, cave_name=args.cave, show_window=args.show_window, seed=args.seed)
    PygameApp(agent=agent, config=config).run()

if __name__ == "__main__":
    main()
