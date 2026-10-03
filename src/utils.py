

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG_DIR = REPO_ROOT / "config"


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a consistent format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                               datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stations_config(path: Path | None = None) -> dict[str, Any]:
    """Load config/stations.yaml."""
    path = path or (CONFIG_DIR / "stations.yaml")
    return load_yaml(path)


def load_parameters_config(path: Path | None = None) -> dict[str, Any]:
    """Load config/parameters.yaml."""
    path = path or (CONFIG_DIR / "parameters.yaml")
    return load_yaml(path)


def resolve_path(relative_path: str) -> Path:
    """Resolve a path stored in a config file (relative to REPO_ROOT)."""
    p = Path(relative_path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p
