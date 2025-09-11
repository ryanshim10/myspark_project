"""Generic UVC camera adapter (stub)."""
from .camera_adapter import CameraAdapter


class UVCAdapter(CameraAdapter):
    def __init__(self, index: int = 0):
        self.index = index
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def get_frame(self):
        if not self.running:
            return None
        return None
