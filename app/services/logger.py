"""Logging system using minimal loguru stub."""
from __future__ import annotations
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(log_dir / "app.log")
