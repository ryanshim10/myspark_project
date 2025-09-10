"""Camera manager coordinating multiple adapters."""
from __future__ import annotations
import time
from typing import Dict, List
from .camera_adapter import CameraAdapter
from .realsense_adapter import RealSenseAdapter
from .uvc_adapter import UVCAdapter
from loguru import logger
from app.utils.error_handling import safe_get_frame


class CameraManager:
    """Manages camera lifecycle with retry logic."""

    def __init__(self):
        self.adapters: Dict[str, CameraAdapter] = {}

    def add_realsense(self, name: str, serial: str | None = None):
        self.adapters[name] = RealSenseAdapter(serial)

    def add_uvc(self, name: str, index: int = 0):
        self.adapters[name] = UVCAdapter(index)

    def start_all(self, attempts: int = 5):
        for name, adapter in self.adapters.items():
            delay = 1.0
            for attempt in range(1, attempts + 1):
                try:
                    adapter.start()
                    logger.info(f"Started {name} on attempt {attempt}")
                    break
                except Exception as exc:  # pragma: no cover - only for real devices
                    logger.warning(f"{name} start failed: {exc}; retrying in {delay}s")
                    time.sleep(delay)
                    delay *= 2
            else:  # no break
                logger.error(f"Failed to start {name} after {attempts} attempts")

    def stop_all(self):
        for name, adapter in self.adapters.items():
            try:
                adapter.stop()
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.error(f"Failed to stop {name}: {exc}")

    def get_frames(self) -> Dict[str, object]:
        return {name: safe_get_frame(adapter) for name, adapter in self.adapters.items()}
