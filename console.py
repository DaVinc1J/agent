"""
Author: Dr Zhibin Liao
Organisation: School of Computer Science and Information Technology, Adelaide University
Date: 26-Apr-2026
Description: This Python script includes a vibe coded Wumpus world game emulator.
Do not change this file, your version of this file won't be used in Gradescope Autographing.

The script is a part of Assignment 3 made for the course ARTI 2003 Artificial Intelligence for the year
of 2026. Public distribution of this source code is strictly forbidden.
"""

import os
from contextlib import nullcontext, redirect_stdout
from collections import deque
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from agent import Agent
from cave import Cave
from definitions import ACTIONS, DIRECTIONS, SENSE_NAMES, VECTORS
from utils import load_config


class WumpusGame:
    def __init__(self, agent=None, config=None):
        """Create a game controller with an agent and config-backed settings."""
        self.config = config if config is not None else load_config()
        self.cave_config = self.config["cave"]
        self.scoring = self.config["scoring"]
        self.emulator_config = self.config["emulator"]
        self.agent = agent if agent is not None else Agent()
        self.new_game()

    def new_game(self):
        """Reset the cave, player state, score, percepts, and agent state."""
        self.cave = Cave(
            width=self.cave_config.get("width"),
            height=self.cave_config.get("height"),
            pit_probability=self.cave_config["pit_probability"],
            min_pits=self.cave_config["pits"]["min"],
            max_pits=self.cave_config["pits"]["max"],
            min_gold=self.cave_config["gold"]["min"],
            max_gold=self.cave_config["gold"]["max"],
            has_wumpus=self.cave_config["wumpus"],
            seed=self.cave_config["seed"],
            map_file=self.cave_config.get("map_file"),
            start=self.cave_config.get("start"),
        )
        self.agent.reset()
        self.start_location = self.cave.start
        self.position = self.start_location
        self.direction = "E"
        self.has_arrow = True
        self.arrow_target = None
        self.gold_remaining = set(self.cave.golds)
        self.gold_collected_locations = set()
        self.gold_collected = 0
        self.has_gold = False
        self.wumpus_alive = True
        self.alive = True
        self.finished = False
        self.score = 0
        self.visited = {self.start_location}
        self.last_bump = False
        self.bumped_walls = set()
        self.last_scream = False
        self.message = f"Explore the cave, find gold, and exit at {self._format_location(self.start_location)}."
        self.log = deque(maxlen=self.emulator_config["recent_percepts_limit"])
        if self.emulator_config["save_last_map"]:
            self.dump_map(self.emulator_config["last_map_file"])

    def dump_map(self, path=None):
        """Write the current cave layout as a reloadable text map."""
        map_path = Path(path) if path is not None else Path(__file__).resolve().parent / "maps" / "last.txt"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            "# Text map rows are written top-to-bottom.",
            "# Markers: S=start/empty, .=empty, W=Wumpus, P=pit, G=gold.",
        ]
        for row in range(self.cave.height - 1, -1, -1):
            markers = []
            for col in range(self.cave.width):
                cell = (row, col)
                if cell == self.start_location:
                    markers.append("S")
                elif cell == self.cave.wumpus:
                    markers.append("W")
                elif cell in self.cave.pits:
                    markers.append("P")
                elif cell in self.cave.golds:
                    markers.append("G")
                else:
                    markers.append(".")
            rows.append("".join(markers))
        map_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return map_path

    def senses(self):
        """Return the current percepts keyed by sense name."""
        stench = self.wumpus_alive and any(cell == self.cave.wumpus for cell in self.cave.adjacent(self.position))
        breeze = any(cell in self.cave.pits for cell in self.cave.adjacent(self.position))
        glimmer = self.position in self.gold_remaining
        senses = {
            "Stench": stench,
            "Breeze": breeze,
            "Glimmer": glimmer,
            "Bump": self.last_bump,
            "Scream": self.last_scream,
        }
        self.last_bump = False
        self.last_scream = False
        return senses

    def apply_action(self, action):
        """Apply one agent action to the world."""
        if self.finished:
            return False

        if action not in ACTIONS:
            self.message = f"Unknown action: {action}"
            return False

        if action == "NO_ACTION":
            self.score += self.scoring["no_action"]
            return False
        else:
            self.score += self.scoring["action"]
            self.message = action.title()

        if action == "LEFT":
            self.direction = DIRECTIONS[(DIRECTIONS.index(self.direction) - 1) % 4]
        elif action == "RIGHT":
            self.direction = DIRECTIONS[(DIRECTIONS.index(self.direction) + 1) % 4]
        elif action == "FORWARD":
            d_row, d_col = VECTORS[self.direction]
            nxt = (self.position[0] + d_row, self.position[1] + d_col)
            if not self.cave.in_bounds(nxt):
                self.last_bump = True
                self.bumped_walls.add(nxt)
                self.message = "Bump: cave wall."
            else:
                self.position = nxt
                self.visited.add(nxt)
                self._resolve_hazards()
        elif action == "SHOOT":
            self._shoot_arrow()
            self.score += self.scoring["shoot"]
        elif action == "GRAB":
            if self.position in self.gold_remaining:
                self.gold_remaining.remove(self.position)
                self.gold_collected_locations.add(self.position)
                self.gold_collected += 1
                self.has_gold = self.gold_collected > 0
                self.score += self.scoring["gold"]
                self.message = f"Gold collected ({self.gold_collected}/{len(self.cave.golds)})."
            else:
                self.message = "There is no gold here."
        elif action == "EXIT":
            if self.position == self.start_location:
                self.finished = True
                self.message = "Exited the cave."
            else:
                self.message = f"Exit is only at {self._format_location(self.start_location)}."

        return True

    def _resolve_hazards(self):
        """End the game if the player has moved onto a pit or living Wumpus."""
        if self.position in self.cave.pits:
            self.alive = False
            self.finished = True
            self.score += self.scoring["death"]
            self.message = "The player fell into a pit."
        elif self.position == self.cave.wumpus and self.wumpus_alive:
            self.alive = False
            self.finished = True
            self.score += self.scoring["death"]
            self.message = "The Wumpus ate the player."

    def _shoot_arrow(self):
        """Fire the arrow one cell forward and kill the Wumpus on a direct hit."""
        if not self.has_arrow:
            self.message = "No arrow left."
            return
        self.has_arrow = False
        d_row, d_col = VECTORS[self.direction]
        target = (self.position[0] + d_row, self.position[1] + d_col)
        self.arrow_target = target
        if target == self.cave.wumpus and self.wumpus_alive:
            self.wumpus_alive = False
            self.last_scream = True
            self.message = "Scream: the Wumpus is dead."
        else:
            self.message = "The arrow missed."

    def log_senses(self, action, senses, start_position=None):
        """Record a timestamped action and percept entry for the side panel."""
        active = [name for name in SENSE_NAMES if senses[name]]
        timestamp = datetime.now().strftime("%H:%M:%S")
        location = self._format_location(start_position or self.position)
        if action == "FORWARD":
            action_text = f"FORWARD -> {self._format_location(self.position)}"
        else:
            action_text = action
        self.log.appendleft(f"[{timestamp}] at: {location} act: {action_text} senses: {', '.join(active) if active else 'none'}")

    def _format_location(self, cell):
        """Format a zero-based (row, column) coordinate as a one-based display coordinate."""
        return f"[{cell[0] + 1},{cell[1] + 1}]"


class Button:
    def __init__(self, rect, label, action):
        """Store the rectangle, label, and command represented by a UI button."""
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action

    def draw(self, screen, font, mouse_pos):
        """Draw the button with a hover highlight when the mouse is over it."""
        hovered = self.rect.collidepoint(mouse_pos)
        color = (244, 246, 248) if hovered else (225, 231, 236)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (40, 48, 56), self.rect, 2, border_radius=8)
        text = font.render(self.label, True, (24, 32, 40))
        screen.blit(text, text.get_rect(center=self.rect.center))


class PygameApp:
    def __init__(self, agent=None, config=None):
        """Create the pygame window and bind it to a WumpusGame instance."""
        self.config = config if config is not None else load_config()
        self.agent = agent if agent is not None else Agent()
        emulator_config = self.config["emulator"]
        self.show_window = emulator_config.get("show_window", True)
        self.base_width = emulator_config["window_width"]
        self.base_height = emulator_config["window_height"]
        self.width = self.base_width
        self.height = self.base_height
        self.board_left = emulator_config["board_left"]
        self.board_top = emulator_config["board_top"]
        self.max_cell = emulator_config["cell_size"]
        self.panel_gap = 26
        self.right_margin = 38
        self.bottom_margin = 30
        self.legend_gap = 22
        self.legend_height = 152
        self.panel_width = 472
        self.panel_top = 70
        self.panel_height = self.base_height - self.panel_top - 20
        self.legend_top = self.base_height - self.bottom_margin - self.legend_height
        self.game = WumpusGame(agent=self.agent, config=self.config)
        self.cell = self.max_cell
        self.panel_left = 0
        self.reveal = False
        self.agent_action_delay_ms = emulator_config["agent_action_delay_ms"]
        self.last_agent_action_time = -self.agent_action_delay_ms
        self.screen = None
        self.clock = None
        self.title_font = None
        self.font = None
        self.small_font = None
        self.percept_font = None
        self.assets = {}
        self.buttons = []
        self._refresh_layout()
        if self.show_window:
            self._init_pygame_window()

    def _init_pygame_window(self):
        """Initialize pygame display resources for visual mode."""
        pygame.init()
        pygame.display.set_caption("Wumpus World Emulator")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 42)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.percept_font = pygame.font.Font(None, 18)
        self.assets = self._load_assets()
        self._refresh_buttons()

    def run(self):
        """Run the visual or silent emulator loop and return the final score."""
        if not self.show_window:
            return self._run_silent()

        return self._run_visual()

    def _run_visual(self):
        """Run the main pygame loop for events, agent actions, and drawing."""
        self.running = True

        while self.running:
            while self.running and not self.game.finished:
                self.clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.handle_key(event.key)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_click(event.pos)

                if not self.game.log:
                    senses = self.game.senses()
                    self.agent.update(senses)
                    self.game.log_senses("Start", senses)

                if self._agent_action_ready():
                    action = self.agent.act()
                    if action:
                        start_position = self.game.position
                        action_applied = self.game.apply_action(action)
                        if action_applied:
                            senses = self.game.senses()
                            self.agent.update(senses)
                            self.game.log_senses(action, senses, start_position=start_position)
                            self.last_agent_action_time = pygame.time.get_ticks()
                    else:
                        raise ValueError('Agent must not return None as an action. If no action is required, return "NO_ACTION"')

                self.draw()
            self.game.finished = True
            while self.running and self.game.finished:
                self.clock.tick(60)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        self.handle_key(event.key)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_click(event.pos)

                self.draw()
        pygame.quit()
        return self.game.score

    def _run_silent(self):
        """Run one complete agent game without opening a pygame window."""
        max_actions = self.config["emulator"].get("max_agent_actions", 1000)
        suppress_output = self.config["emulator"].get("suppress_agent_output", True)
        output_context = open(os.devnull, "w", encoding="utf-8") if suppress_output else None
        redirect_context = redirect_stdout(output_context) if output_context is not None else nullcontext()

        try:
            with redirect_context:
                if not self.game.log:
                    senses = self.game.senses()
                    self.agent.update(senses)
                    self.game.log_senses("Start", senses)

                actions_taken = 0
                while not self.game.finished and actions_taken < max_actions:
                    action = self.agent.act()
                    if not action:
                        raise ValueError('Agent must not return None as an action. If no action is required, return "NO_ACTION"')

                    start_position = self.game.position
                    action_applied = self.game.apply_action(action)
                    if action_applied:
                        senses = self.game.senses()
                        self.agent.update(senses)
                        self.game.log_senses(action, senses, start_position=start_position)

                    actions_taken += 1

                if not self.game.finished and actions_taken >= max_actions:
                    self.game.message = f"Stopped after {max_actions} actions."
        finally:
            if output_context is not None:
                output_context.close()

        return self.game.score, self.game.message

    def handle_key(self, key):
        """Handle emulator-level keyboard shortcuts such as new cave and reveal."""
        if key == pygame.K_n:
            self._new_game()
        elif key == pygame.K_r:
            self.reveal = not self.reveal

    def handle_click(self, pos):
        """Handle mouse clicks on right-panel interface buttons."""
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                if button.action == "new":
                    self._new_game()
                elif button.action == "reveal":
                    self.reveal = not self.reveal
                elif button.action == "exit":
                    self.running = False

    def _new_game(self):
        """Start a fresh cave and refresh the display layout around its size."""
        self.game.new_game()
        self._refresh_layout()
        self.last_agent_action_time = -self.agent_action_delay_ms
        if self.show_window and self.screen is not None:
            self._refresh_buttons()

    def _agent_action_ready(self):
        """Return True when enough time has passed for another agent action."""
        return pygame.time.get_ticks() - self.last_agent_action_time >= self.agent_action_delay_ms

    def _refresh_layout(self):
        """Recompute board and panel geometry within the fixed emulator window."""
        self.width = self.base_width
        self.height = self.base_height
        self.panel_left = self.width - self.panel_width - self.right_margin
        self.cell = self._display_cell_size()

    def _refresh_buttons(self):
        """Place the top-right buttons based on the current right panel position."""
        button_top = 86
        x = self.panel_left + 30
        self.buttons = [
            Button((x, button_top, 140, 42), "New Cave", "new"),
            Button((x + 156, button_top, 140, 42), "Reveal: Off", "reveal"),
            Button((x + 312, button_top, 110, 42), "Exit Game", "exit"),
        ]

    def draw(self):
        """Redraw the complete game window for the current frame."""
        self.screen.fill((246, 247, 241))
        self.draw_header()
        self.draw_board()
        self.draw_legend_panel()
        self.draw_panel()
        pygame.display.flip()

    def draw_header(self):
        """Draw the window title."""
        title = self.title_font.render("Wumpus World Emulator", True, (30, 38, 46))
        self.screen.blit(title, (48, 24))

    def draw_board(self):
        """Draw the cave grid, visible cell contents, and the agent."""
        self.draw_wall_border()

        for row in range(self.game.cave.height - 1, -1, -1):
            for col in range(self.game.cave.width):
                rect = self._cell_rect((row, col))
                cell = (row, col)
                explored = cell in self.game.visited
                visible = self.reveal or explored
                if cell == self.game.start_location:
                    base = (252, 239, 173)
                elif explored:
                    base = (228, 235, 222)
                elif self.reveal:
                    base = (203, 211, 213)
                else:
                    base = (203, 211, 213)
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (75, 85, 92), rect, 2)
                self.draw_cell_index(rect, cell, (80, 89, 94))

                if visible:
                    self.draw_contents(rect, cell)
                    self.draw_senses(rect, cell)

        self.draw_agent()

    def draw_wall_border(self):
        """Draw a half-cell-thick wall border around the cave."""
        wall = self._wall_thickness()
        left = self.board_left
        top = self.board_top
        cave_width = self.game.cave.width * self.cell
        cave_height = self.game.cave.height * self.cell
        right = left + wall + cave_width
        bottom = top + wall + cave_height

        for col in range(self.game.cave.width):
            x = left + wall + col * self.cell
            self.draw_wall_cell(pygame.Rect(x, top, self.cell, wall), (self.game.cave.height, col))
            self.draw_wall_cell(pygame.Rect(x, bottom, self.cell, wall), (-1, col))

        for row in range(self.game.cave.height):
            y = top + wall + row * self.cell
            display_row = self.game.cave.height - 1 - row
            self.draw_wall_cell(pygame.Rect(left, y, wall, self.cell), (display_row, -1))
            self.draw_wall_cell(pygame.Rect(right, y, wall, self.cell), (display_row, self.game.cave.width))

        self.draw_wall_cell(pygame.Rect(left, top, wall, wall), (self.game.cave.height, -1))
        self.draw_wall_cell(pygame.Rect(right, top, wall, wall), (self.game.cave.height, self.game.cave.width))
        self.draw_wall_cell(pygame.Rect(left, bottom, wall, wall), (-1, -1))
        self.draw_wall_cell(pygame.Rect(right, bottom, wall, wall), (-1, self.game.cave.width))

    def draw_wall_cell(self, rect, cell):
        """Draw one visible wall segment around the cave boundary."""
        bumped = cell in self.game.bumped_walls
        fill = (132, 86, 49) if bumped else (101, 109, 114)
        border = (82, 50, 27) if bumped else (58, 65, 70)
        inner_fill = (160, 105, 61) if bumped else (126, 135, 140)
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, border, rect, 2)
        inset = max(2, min(rect.width, rect.height) // 5)
        inner = rect.inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(self.screen, inner_fill, inner, border_radius=4)
        self.draw_cell_index(rect, cell, (230, 234, 236))
        if cell == self.game.arrow_target:
            self.draw_asset("arrow", rect)

    def draw_cell_index(self, rect, cell, color):
        """Draw a one-based row/column index label in a cave or wall cell."""
        row, col = cell
        coord = self.small_font.render(f"[{row + 1},{col + 1}]", True, color)
        margin = max(3, min(8, min(rect.width, rect.height) // 7))
        self.screen.blit(coord, (rect.x + margin, rect.y + margin))

    def draw_senses(self, rect, cell):
        """Draw percept labels inside a visible cell."""
        labels = []
        if self.game.wumpus_alive and any(n == self.game.cave.wumpus for n in self.game.cave.adjacent(cell)):
            labels.append(("Stench", (34, 139, 34)))
        if any(n in self.game.cave.pits for n in self.game.cave.adjacent(cell)):
            labels.append(("Breeze", (74, 174, 232)))
        if cell in self.game.gold_remaining:
            labels.append(("Glimmer", (148, 111, 16)))
        for i, (label, color) in enumerate(labels[:3]):
            text = self.percept_font.render(label, True, color)
            x = rect.x + 8
            y = rect.bottom - 8 - text.get_height() - i * 15
            self.screen.blit(text, (x, y))

    def draw_contents(self, rect, cell):
        """Draw pits, Wumpus, and gold icons inside a visible cell."""
        if cell in self.game.cave.pits:
            self.draw_asset("hole", rect)
        if cell == self.game.cave.wumpus:
            asset_name = "wumpus" if self.game.wumpus_alive else "wumpus_dead"
            self.draw_asset(asset_name, rect)
        if cell in self.game.gold_remaining:
            self.draw_asset("gold", rect)
        elif cell in self.game.gold_collected_locations:
            self.draw_asset("gold_collected", rect)
        if cell == self.game.arrow_target:
            self.draw_asset("arrow", rect)

    def draw_asset(self, name, rect):
        """Draw a scaled asset centered in a cave cell."""
        asset = self.assets[name]
        target_size = max(1, int(self.cell * 0.5))
        scaled = pygame.transform.smoothscale(asset, (target_size, target_size))
        self.screen.blit(scaled, scaled.get_rect(center=rect.center))

    def draw_agent(self):
        """Draw the player triangle at the current position and facing."""
        rect = self._cell_rect(self.game.position)
        cx, cy = rect.center
        color = (32, 91, 86) if self.game.alive else (120, 124, 126)
        points = self._agent_triangle(cx, cy, self.game.direction)
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (242, 246, 245), points, 3)
        pygame.draw.circle(self.screen, (250, 250, 250), (cx, cy), max(3, self.cell // 18))

    def draw_legend_panel(self):
        """Draw the lower panel containing human controls and percept meanings."""
        panel = pygame.Rect(
            self.board_left,
            self.legend_top,
            self.panel_left - self.board_left - self.panel_gap,
            self.legend_height,
        )
        pygame.draw.rect(self.screen, (251, 251, 248), panel, border_radius=8)
        pygame.draw.rect(self.screen, (94, 104, 112), panel, 2, border_radius=8)

        x = panel.x + 18
        y = panel.y + 16
        controls_heading = self.font.render("Human Controls", True, (35, 43, 50))
        self.screen.blit(controls_heading, (x, y))
        y += 24
        controls = "Forward: Space, Turns: Arrow keys, Shoot: Z, Grab: X, Exit: Q, New Cave: N, Reveal: R"
        for line in self._wrap(controls, 62):
            text = self.small_font.render(line, True, (72, 82, 89))
            self.screen.blit(text, (x, y))
            y += 20

        y += 8
        percept_heading = self.font.render("Percepts", True, (35, 43, 50))
        self.screen.blit(percept_heading, (x, y))
        y += 24
        legend = "Stench near Wumpus, Breeze near pit, Glimmer on gold, Bump at wall, Scream after an arrow hits a Wumpus and it dies."
        for line in self._wrap(legend, 72):
            text = self.small_font.render(line, True, (72, 82, 89))
            self.screen.blit(text, (x, y))
            y += 20

    def draw_panel(self):
        """Draw the right-side controls, status values, message, and percept log."""
        panel = pygame.Rect(self.panel_left, self.panel_top, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, (251, 251, 248), panel, border_radius=8)
        pygame.draw.rect(self.screen, (94, 104, 112), panel, 2, border_radius=8)

        mouse = pygame.mouse.get_pos()
        self.buttons[1].label = "Reveal: On" if self.reveal else "Reveal: Off"
        for button in self.buttons:
            button.draw(self.screen, self.font, mouse)

        y = 150
        text_x = self.panel_left + 30
        info = [
            f"Score: {self.game.score}",
            f"Position: [{self.game.position[0] + 1},{self.game.position[1] + 1}]",
            f"Facing: {self.game.direction}",
            f"Arrow: {'carrying' if self.game.has_arrow else 'used'}",
            f"Gold: {self.game.gold_collected}/{len(self.game.cave.golds)}",
            f"State: {'finished' if self.game.finished else 'alive'}",
        ]
        for line in info:
            text = self.font.render(line, True, (35, 43, 50))
            self.screen.blit(text, (text_x, y))
            y += 30

        msg = self._wrap(self.game.message, 42)
        y += 18
        for line in msg:
            text = self.font.render(line, True, (80, 55, 43))
            self.screen.blit(text, (text_x, y))
            y += 26

        y += 18
        heading = self.font.render("Recent percepts", True, (35, 43, 50))
        self.screen.blit(heading, (text_x, y))
        y += 32
        for entry in self.game.log:
            text = self.small_font.render(entry, True, (72, 82, 89))
            self.screen.blit(text, (text_x, y))
            y += 22

    def _cell_rect(self, cell):
        """Convert a cave (row, column) coordinate into its pygame rectangle on screen."""
        row, col = cell
        wall = self._wall_thickness()
        screen_x = self.board_left + wall + col * self.cell
        screen_y = self.board_top + wall + (self.game.cave.height - 1 - row) * self.cell
        return pygame.Rect(screen_x, screen_y, self.cell, self.cell)

    def _display_cell_size(self):
        """Return a cell size that fits the cave plus half-cell walls."""
        display_cols = self.game.cave.width + 1
        display_rows = self.game.cave.height + 1
        available_width = self.panel_left - self.board_left - self.panel_gap
        available_height = self.legend_top - self.board_top - self.legend_gap
        return max(32, min(self.max_cell, available_width // display_cols, available_height // display_rows))

    def _wall_thickness(self):
        """Return the wall thickness as half of one cave cell."""
        return max(1, self.cell // 2)

    def _load_assets(self):
        """Load raster assets used for cave contents."""
        asset_dir = Path(__file__).resolve().parent / "assets"
        return {
            "arrow": pygame.image.load(asset_dir / "arrow.png").convert_alpha(),
            "gold": pygame.image.load(asset_dir / "gold.png").convert_alpha(),
            "gold_collected": pygame.image.load(asset_dir / "gold_collected.png").convert_alpha(),
            "hole": pygame.image.load(asset_dir / "hole.png").convert_alpha(),
            "wumpus": pygame.image.load(asset_dir / "wumpus.png").convert_alpha(),
            "wumpus_dead": pygame.image.load(asset_dir / "wumpus_dead.png").convert_alpha(),
        }

    def _agent_triangle(self, cx, cy, direction):
        """Return triangle points for drawing the agent in the facing direction."""
        tip = max(8, int(self.cell * 0.25))
        half_base = max(6, int(self.cell * 0.18))
        back = max(6, int(self.cell * 0.18))
        if direction == "N":
            return [(cx, cy - tip), (cx - half_base, cy + back), (cx + half_base, cy + back)]
        if direction == "S":
            return [(cx, cy + tip), (cx - half_base, cy - back), (cx + half_base, cy - back)]
        if direction == "E":
            return [(cx + tip, cy), (cx - back, cy - half_base), (cx - back, cy + half_base)]
        return [(cx - tip, cy), (cx + back, cy - half_base), (cx + back, cy + half_base)]

    def _wrap(self, text, width):
        """Wrap a text string into lines no longer than the requested width."""
        words = text.split()
        lines = []
        current = []
        for word in words:
            if sum(len(w) + 1 for w in current) + len(word) > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines


def main():
    """Tell users to start the emulator through an agent module."""
    raise SystemExit("Run an agent module, for example: python my_agent.py")


if __name__ == "__main__":
    main()
