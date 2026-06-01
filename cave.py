"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script includes the Cave generation for the Wumpus World.
Do not change this file, your version of this file won't be used in Gradescope Autographing.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

import random
from pathlib import Path

from definitions import VECTORS


class Cave:
    def __init__(
        self,
        width=None,
        height=None,
        pit_probability=0.18,
        min_pits=1,
        max_pits=4,
        min_gold=1,
        max_gold=1,
        has_wumpus=True,
        seed=None,
        map_file=None,
        start=None,
    ):
        """Create a generated cave or load one from a text map."""
        self.random = random.Random(seed)
        self.width = width if width is not None else (None if map_file else 4)
        self.height = height if height is not None else (None if map_file else 4)
        self.start_spec = start if start is not None or map_file else {"row": 1, "col": 1}
        self.start = None
        self.pit_probability = pit_probability
        self.min_pits = max(0, min_pits)
        self.max_pits = max(0, max_pits)
        self.min_gold = max(0, min_gold)
        self.max_gold = max(0, max_gold)
        self.has_wumpus = has_wumpus
        self.map_file = map_file
        if self.map_file:
            self.load_map(self.map_file)
        else:
            self._resolve_dimensions()
            self.start = self._sample_start()
            self.generate()

    def generate(self):
        """Place the Wumpus, gold pieces, and pits without overlapping them."""
        cells = [(row, col) for row in range(self.height) for col in range(self.width) if (row, col) != self.start]
        if not cells and self.has_wumpus:
            raise ValueError("Cave must contain at least one non-start cell.")
        self.wumpus = self.random.choice(cells) if self.has_wumpus else None
        gold_options = [cell for cell in cells if cell != self.wumpus]
        min_gold = min(self.min_gold, len(gold_options))
        max_gold = min(max(self.max_gold, min_gold), len(gold_options))
        gold_count = self.random.randint(min_gold, max_gold)
        self.golds = set(self.random.sample(gold_options, gold_count))
        self.gold = next(iter(self.golds)) if self.golds else None

        hazard_options = [cell for cell in cells if cell != self.wumpus and cell not in self.golds]
        pit_candidates = [
            cell
            for cell in hazard_options
            if self.random.random() < self.pit_probability
        ]
        min_pits = min(self.min_pits, len(hazard_options))
        max_pits = min(max(self.max_pits, min_pits), len(hazard_options))
        if len(pit_candidates) < min_pits:
            extra_options = [cell for cell in hazard_options if cell not in pit_candidates]
            pit_candidates.extend(self.random.sample(extra_options, min_pits - len(pit_candidates)))
        pit_count = self.random.randint(min_pits, min(max_pits, len(pit_candidates)))
        self.pits = set(self.random.sample(pit_candidates, pit_count))

    def load_map(self, map_file):
        """Load Wumpus, pit, and gold positions from a text map file."""
        path = Path(map_file)
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not lines:
            raise ValueError(f"Map {path} must contain at least one non-comment row.")
        map_width = len(lines[0])
        if map_width == 0 or any(len(line) != map_width for line in lines):
            raise ValueError(f"Map {path} must have the same number of columns on every row.")
        resolved_width = self._resolve_dimension_spec(self.width, "width", default=map_width)
        resolved_height = self._resolve_dimension_spec(self.height, "height", default=len(lines))
        if len(lines) != resolved_height:
            raise ValueError(f"Map {path} has {len(lines)} rows, expected {resolved_height}.")
        if any(len(line) != resolved_width for line in lines):
            raise ValueError(f"Map {path} must have exactly {resolved_width} columns per row.")
        self.width = resolved_width
        self.height = resolved_height
        if self.start is None:
            self.start = self._sample_start(default=self._find_map_start(lines))

        self.wumpus = None
        self.golds = set()
        self.pits = set()
        for file_row, line in enumerate(lines):
            row = self.height - 1 - file_row
            for col, marker in enumerate(line):
                self._load_marker(marker, (row, col), path)
        self.gold = next(iter(self.golds)) if self.golds else None

    def _load_marker(self, marker, cell, path):
        """Apply one text-map marker to the cave contents."""
        if cell == self.start and marker in {"P", "W", "G"}:
            raise ValueError(f"Map {path} cannot place {marker} at the start.")
        if marker in {".", "S"}:
            return
        if marker == "P":
            self.pits.add(cell)
            return
        if marker == "G":
            self.golds.add(cell)
            return
        if marker == "W":
            if self.wumpus is not None:
                raise ValueError(f"Map {path} contains more than one Wumpus.")
            self.wumpus = cell
            return
        raise ValueError(f"Map {path} contains unsupported marker: {marker}")

    def _resolve_dimensions(self):
        """Resolve width and height specs into concrete positive integers."""
        self.width = self._resolve_dimension_spec(self.width, "width", default=4)
        self.height = self._resolve_dimension_spec(self.height, "height", default=4)

    def _resolve_dimension_spec(self, value, name, default):
        """Resolve one cave dimension from an integer or min/max spec."""
        if value is None:
            return default
        if isinstance(value, int):
            resolved = value
        elif isinstance(value, dict):
            min_value = value.get("min")
            max_value = value.get("max", min_value)
            resolved = self._sample_dimension_range(min_value, max_value, name)
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            resolved = self._sample_dimension_range(value[0], value[1], name)
        else:
            raise ValueError(f"Cave {name} must be an integer or a two-point range.")
        if resolved <= 0:
            raise ValueError(f"Cave {name} must be positive.")
        return resolved

    def _sample_dimension_range(self, min_value, max_value, name):
        """Sample one cave dimension from a validated inclusive range."""
        if min_value is None or max_value is None:
            raise ValueError(f"Cave {name} range must define min and max.")
        min_value = int(min_value)
        max_value = int(max_value)
        if min_value <= 0 or max_value <= 0:
            raise ValueError(f"Cave {name} must be positive.")
        if min_value > max_value:
            raise ValueError(f"Cave {name} min cannot be greater than max.")
        return self.random.randint(min_value, max_value)

    def _sample_start(self, default=(0, 0)):
        """Return one configured start cell sampled from the available options."""
        options = self._resolve_start_options()
        if not options:
            return default
        return self.random.choice(options)

    def _resolve_start_options(self):
        """Resolve start specs into valid zero-based cells for the current cave size."""
        if self.start_spec is None:
            return []
        start = self.start_spec
        if isinstance(start, list):
            if not start:
                raise ValueError("Cave start list must not be empty.")
            if len(start) == 2 and all(not isinstance(value, (dict, list, tuple)) for value in start):
                candidates = [start]
            else:
                candidates = start
        else:
            candidates = [start]

        options = []
        for candidate in candidates:
            if isinstance(candidate, dict):
                display_row = candidate.get("row", 1)
                display_col = candidate.get("col", candidate.get("column", 1))
            elif isinstance(candidate, (list, tuple)) and len(candidate) == 2:
                display_row, display_col = candidate
            else:
                raise ValueError("Each cave start option must be a mapping or two-item list.")
            row = self._resolve_start_axis(display_row, self.height, "row") - 1
            col = self._resolve_start_axis(display_col, self.width, "col") - 1
            if 0 <= row < self.height and 0 <= col < self.width:
                options.append((row, col))
        if self.start_spec is not None and not options:
            raise ValueError(f"No cave start options fit inside the {self.height}x{self.width} cave.")
        return options

    def _resolve_start_axis(self, value, upper_bound, name):
        """Resolve one one-based start axis from an integer-like value or the token 'max'."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "max":
                return upper_bound
            raise ValueError(f"Cave start {name} must be an integer or 'max'.")
        resolved = int(value)
        if resolved <= 0:
            raise ValueError(f"Cave start {name} must be positive.")
        return resolved

    def _find_map_start(self, lines):
        """Return the zero-based start cell marked by S in top-to-bottom map rows."""
        starts = []
        for file_row, line in enumerate(lines):
            row = self.height - 1 - file_row
            for col, marker in enumerate(line):
                if marker == "S":
                    starts.append((row, col))
        if len(starts) > 1:
            raise ValueError("Map cannot contain more than one start marker.")
        return starts[0] if starts else (0, 0)

    def in_bounds(self, cell):
        """Return True when a cell coordinate is inside the cave grid."""
        row, col = cell
        return 0 <= row < self.height and 0 <= col < self.width

    def adjacent(self, cell):
        """Yield non-diagonal neighboring cells that are inside the cave."""
        row, col = cell
        for d_row, d_col in VECTORS.values():
            nxt = (row + d_row, col + d_col)
            if self.in_bounds(nxt):
                yield nxt
