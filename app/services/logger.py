"""Logging system using minimal loguru stub.

This helper sets up loguru so that the application writes log messages to a
rotating file.  Even though the bundled :mod:`loguru` implementation is a very
small stub, it honours the ``add`` options we pass in, making it possible to
describe our intent for the real dependency used in production.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path) -> None:
    """Configure loguru with daily rotation and 7‑day retention.

    Parameters
    ----------
    log_dir:
        Directory where log files should be written.  The function ensures the
        directory exists and configures loguru to write to ``app.log`` with
        midnight rotation.  Old log files are kept for seven days.
    """

    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    log_path = log_dir / "app.log"
    # Rotate at midnight, keep a week's worth of logs and use async writes to
    # avoid blocking the UI thread.
    logger.add(log_path, rotation="00:00", retention=7, enqueue=True)
