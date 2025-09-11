from app.utils.error_handling import safe_get_frame
from app.camera.camera_manager import CameraManager


class FailingCam:
    def start(self):
        pass

    def stop(self):
        pass

    def get_frame(self):
        raise RuntimeError("boom")


def test_safe_get_frame_returns_black():
    frame = safe_get_frame(FailingCam(), (2, 3))
    assert frame == [[0, 0, 0], [0, 0, 0]]


def test_camera_manager_black_frame():
    cm = CameraManager()
    cm.adapters["cam1"] = FailingCam()
    frames = cm.get_frames()
    assert frames["cam1"][0][0] == 0
