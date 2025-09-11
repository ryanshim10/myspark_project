from datetime import datetime
from app.pipeline.capture_pipeline import CapturePipeline


def test_capture_pipeline(tmp_path):
    pipeline = CapturePipeline(tmp_path)
    frames = {"CAM1": object()}
    ts = datetime(2024, 1, 2, 3, 4, 5)
    paths = pipeline.capture(frames, "OK", ts)
    assert len(paths) == 1
    assert paths[0].exists()
    assert paths[0].name == "2024_0102_030405_CAM1_OK.jpg"
