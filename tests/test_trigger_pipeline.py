from app.pipeline.trigger_pipeline import TriggerPipeline, ROI


def test_trigger_pipeline_basic():
    depth = [[1, 1], [1, 1]]
    roi = ROI(0, 0, 2, 2)
    pipeline = TriggerPipeline([roi], min_z=0.5, max_z=1.5, threshold=0.9)
    assert pipeline.evaluate(depth) is True
