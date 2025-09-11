"""Utility for safe frame retrieval with fallback."""
from __future__ import annotations
from loguru import logger
from typing import Tuple, List


def _black_frame(shape: Tuple[int, int]) -> List[List[int]]:
    """Create a black (zero) frame as nested lists.

    Parameters
    ----------
    shape:
        (height, width) of the frame to create.
    """

    height, width = shape
    return [[0 for _ in range(width)] for _ in range(height)]


def safe_get_frame(camera, fallback_shape: Tuple[int, int] = (480, 640)):
    """Retrieve a frame, returning a black fallback on failure.

    Any exception raised by ``camera.get_frame`` is caught and logged.  A
    black frame of ``fallback_shape`` is returned instead so that callers can
    continue operating without special‑casing failures.
    """

    try:
        frame = camera.get_frame()
        if frame is None:
            raise ValueError("no frame")
        return frame
    except Exception as exc:  # pragma: no cover - exercised in unit tests
        logger.error(f"Frame retrieval failed: {exc}")
        return _black_frame(fallback_shape)
