"""Intel RealSense camera adapter (stub)."""
from .camera_adapter import CameraAdapter


class RealSenseAdapter(CameraAdapter):
    def __init__(self, serial: str | None = None):
        self.serial = serial
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def get_frame(self):
        if not self.running:
            return None
        return None
