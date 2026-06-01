"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script includes shared Wumpus World action, sense, and direction definitions.
Do not add your own definitions here, your version of this file won't be used in Gradescope Autographing.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

ACTIONS = ["FORWARD", "LEFT", "RIGHT", "GRAB", "SHOOT", "EXIT", "NO_ACTION"]
SENSE_NAMES = ["Stench", "Breeze", "Glimmer", "Bump", "Scream"]
DIRECTIONS = ["N", "E", "S", "W"]
VECTORS = {
    "N": (1, 0),
    "E": (0, 1),
    "S": (-1, 0),
    "W": (0, -1),
}
