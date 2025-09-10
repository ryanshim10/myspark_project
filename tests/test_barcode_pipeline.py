from app.pipeline import barcode_pipeline
from app.pipeline.barcode_pipeline import BarcodePipeline


def test_barcode_pipeline(monkeypatch, tmp_path):
    pipeline = BarcodePipeline(tmp_path)
    monkeypatch.setattr(barcode_pipeline, "_decode", lambda img: ["12345"])
    res = pipeline.process(None, "test")
    assert res.text == "12345"
    assert res.crop_path.exists()
