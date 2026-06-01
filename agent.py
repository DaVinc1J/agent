"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script shows the basic agent template. MyAgent should be extending this Agent class.
Do not change this file, your version of this file won't be used in Gradescope Autographing.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

from definitions import ACTIONS, SENSE_NAMES


class Agent:
    """Template Wumpus agent.

    This class keeps the emulator-facing state deliberately small. Use it as a
    starting point for an intelligent agent by storing any internal map, rule
    base, or plan you need in reset(), updating it from senses in update(), and
    choosing the next action in act().
    """

    def __init__(self):
        """Create a fresh agent and initialise its state."""
        self.last_senses = None
        self.last_action = None
        self.reset()

    def reset(self):
        """Reset all state before a new cave starts."""
        self.last_senses = None
        self.last_action = None

    def update(self, senses):
        """Receive the latest percept values keyed by sense name."""
        missing = [name for name in SENSE_NAMES if name not in senses]
        if missing:
            raise ValueError(f"Missing sense values: {', '.join(missing)}")
        self.last_senses = {name: bool(senses[name]) for name in SENSE_NAMES}

    def act(self):
        """Return the next action string.

        The base agent is passive so it can be loaded safely in the emulator.
        Assignment agents should override this method and return one of:
        FORWARD, LEFT, RIGHT, GRAB, SHOOT, EXIT, NO_ACTION.
        If no action is given for any reason (say you are changing an internal state),
        the NO_ACTION action should be returned instead.
        """
        return 'NO_ACTION'

    def remember_action(self, action):
        """Store and validate an action before returning it from a subclass."""
        if action is not None and action not in ACTIONS:
            raise ValueError(f"Unknown action: {action}")
        self.last_action = action
        return action
