"""Configuration loading helpers for the Wumpus World project."""

from pathlib import Path

import yaml


def load_config(path="game_config.yaml", cave_name="default", show_window=None, seed=None):
    """Load YAML game settings and select one named cave profile."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Game config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Game config must be a YAML mapping: {config_path}")
    for section in ("scoring", "emulator"):
        if section not in config:
            raise KeyError(f"Missing required config section: {section}")
    if show_window is not None:
        config["emulator"]["show_window"] = _load_bool_override(show_window, "show_window")
    caves = _load_cave_profiles(config, config_path)
    if cave_name not in caves:
        names = ", ".join(sorted(caves))
        raise KeyError(f"Unknown cave profile '{cave_name}'. Available caves: {names}")
    cave_config = caves[cave_name]
    config["selected_cave"] = cave_name
    config["cave"] = cave_config
    if seed is not None:
        cave_config["seed"] = _load_seed_override(seed)
    if cave_config.get("map_file"):
        map_path = Path(cave_config["map_file"])
        if not map_path.is_absolute():
            map_path = config_path.parent / map_path
        cave_config["map_file"] = str(map_path)
        _prepare_map_cave_config(cave_config)
    if config["emulator"].get("last_map_file"):
        last_map_path = Path(config["emulator"]["last_map_file"])
        if not last_map_path.is_absolute():
            last_map_path = config_path.parent / last_map_path
        config["emulator"]["last_map_file"] = str(last_map_path)
    return config


def _load_bool_override(value, name):
    """Return a boolean override loaded from a CLI string or direct bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise ValueError(f"{name} override must be true or false.")


def _load_seed_override(value):
    """Return an integer seed override loaded from CLI text or a direct int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value.strip())
    raise ValueError("seed override must be an integer.")


def _load_cave_profiles(config, config_path):
    """Load named cave profiles from the main config or a referenced YAML file."""
    if "caves" in config:
        caves = config["caves"]
    elif "cave" in config:
        cave_path = _resolve_cave_config_path(config["cave"], config_path)
        if not cave_path.exists():
            raise FileNotFoundError(f"Cave config file not found: {cave_path}")
        with cave_path.open("r", encoding="utf-8") as file:
            cave_config = yaml.safe_load(file)
        if not isinstance(cave_config, dict):
            raise ValueError(f"Cave config must be a YAML mapping: {cave_path}")
        caves = cave_config.get("caves", cave_config)
    else:
        raise KeyError("Missing required config section: cave")
    if not isinstance(caves, dict):
        raise ValueError("Cave profiles must be a YAML mapping.")
    return caves


def _resolve_cave_config_path(cave_entry, config_path):
    """Return the cave config path declared by the main game config."""
    if isinstance(cave_entry, str):
        cave_path = Path(cave_entry)
    elif isinstance(cave_entry, dict):
        raw_path = cave_entry.get("config") or cave_entry.get("path") or cave_entry.get("file")
        if raw_path is None:
            raise KeyError("Cave config entry must define config, path, or file.")
        cave_path = Path(raw_path)
    else:
        raise ValueError("Cave config entry must be a path string or mapping.")
    if not cave_path.is_absolute():
        cave_path = config_path.parent / cave_path
    return cave_path


def _prepare_map_cave_config(cave_config):
    """Fill runtime defaults for caves loaded from a text map."""
    cave_config.setdefault("seed", None)
    cave_config.setdefault("wumpus", True)
    cave_config.setdefault("pit_probability", 0.0)
    cave_config.setdefault("pits", {"min": 0, "max": 0})
    cave_config.setdefault("gold", {"min": 0, "max": 0})
