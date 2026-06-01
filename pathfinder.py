"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script includes independent grid pathfinding helpers for Wumpus World agents.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

from collections import deque
from heapq import heappop, heappush


class Node:
    """A search node with a position, parent pointer, and path cost."""

    def __init__(self, position, parent=None, cost=0):
        """Store a grid position, parent node, and cost to reach it."""
        self.position = position
        self.parent = parent
        self.cost = cost

    def path(self):
        """Return the path from the start node to this node, excluding start."""
        nodes = []
        current = self
        while current.parent is not None:
            nodes.append(current.position)
            current = current.parent
        return list(reversed(nodes))

def bfs(start_position, target_position, map_size, grid):
    """Find the shortest path on a marked grid using breadth-first search.

    Args:
        start_position: Starting coordinate as (row, column).
        target_position: Target coordinate as (row, column).
        map_size: Grid size as (rows, columns).
        grid: A numpy 2D array indexed as grid[row][column], where 1 means traversable
            and "X" means blocked.

    Returns:
        A list of (row, column) coordinates from the first move through the target, or
        None if no path exists.
    """
    start_position = tuple(start_position)
    target_position = tuple(target_position)
    rows, cols = map_size
    if not _in_bounds(start_position, rows, cols) or not _in_bounds(target_position, rows, cols):
        return None
    if not _is_open(start_position, grid) or not _is_open(target_position, grid):
        return None

    queue = deque([Node(start_position)])
    seen = {start_position}

    while queue:
        node = queue.popleft()
        if node.position == target_position:
            return node.path()

        for neighbor in _neighbors(node.position, rows, cols):
            if neighbor in seen or not _is_open(neighbor, grid):
                continue
            seen.add(neighbor)
            queue.append(Node(neighbor, node))

    return None


def ucs(start_position, target_position, map_size, grid):
    """Find the lowest-cost path on a marked grid using uniform-cost search.

    Args:
        start_position: Starting coordinate as (row, column).
        target_position: Target coordinate as (row, column).
        map_size: Grid size as (rows, columns).
        grid: A numpy 2D array indexed as grid[row][column], where real values indicating node travel-through cost
            and "X" means blocked.

    Returns:
        A list of (row, column) coordinates from the first move through the target, or
        None if no path exists.
    """
    start_position = tuple(start_position)
    target_position = tuple(target_position)
    rows, cols = map_size
    if not _in_bounds(start_position, rows, cols) or not _in_bounds(target_position, rows, cols):
        return None
    if not _is_open(start_position, grid) or not _is_open(target_position, grid):
        return None

    counter = 0
    queue = [(0, counter, Node(start_position))]
    best_cost = {start_position: 0}

    while queue:
        cost, _, node = heappop(queue)
        if cost != best_cost[node.position]:
            continue
        if node.position == target_position:
            return node.path()

        for neighbor in _neighbors(node.position, rows, cols):
            if not _is_open(neighbor, grid):
                continue
            new_cost = cost + _move_cost(neighbor, grid)
            if neighbor in best_cost and new_cost >= best_cost[neighbor]:
                continue
            best_cost[neighbor] = new_cost
            counter += 1
            heappush(queue, (new_cost, counter, Node(neighbor, node, new_cost)))

    return None


def _neighbors(position, rows, cols):
    """Yield in-bounds non-diagonal neighbor positions."""
    row, col = position
    for d_row, d_col in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        neighbor = (row + d_row, col + d_col)
        if _in_bounds(neighbor, rows, cols):
            yield neighbor


def _in_bounds(position, rows, cols):
    """Return True when a position lies inside the map dimensions."""
    row, col = position
    return 0 <= row < rows and 0 <= col < cols


def _is_open(position, grid):
    """Return True when the grid cell is marked as traversable."""
    row, col = position
    return grid[row][col] != "X"


def _move_cost(position, grid):
    """Return the cost of entering a traversable grid cell."""
    row, col = position
    return grid[row][col]
