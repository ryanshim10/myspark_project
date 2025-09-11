"""Camera adapter interface."""
from abc import ABC, abstractmethod


class CameraAdapter(ABC):
    """Unified interface for camera devices."""

    @abstractmethod
    def start(self):
        """Start camera streaming."""

    @abstractmethod
    def stop(self):
        """Stop camera streaming."""

    @abstractmethod
    def get_frame(self):
        """Return a frame as numpy array."""
