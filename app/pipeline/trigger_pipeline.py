"""Depth ROI trigger pipeline without numpy dependency."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class ROI:
    x: int
    y: int
    w: int
    h: int


class TriggerPipeline:
    """Computes inlier ratios over multiple ROIs."""

    def __init__(self, rois: List[ROI], min_z: float, max_z: float, threshold: float = 0.95, window: int = 5):
        self.rois = rois
        self.min_z = min_z
        self.max_z = max_z
        self.threshold = threshold
        self.window = window
        self.history: List[float] = []

    def _compute_roi_ratio(self, depth: List[List[float]], roi: ROI) -> float:
        region = [row[roi.x : roi.x + roi.w] for row in depth[roi.y : roi.y + roi.h]]
        total = roi.w * roi.h
        inliers = sum(self.min_z <= v <= self.max_z for row in region for v in row)
        return inliers / total if total else 0.0

    def evaluate(self, depth: List[List[float]]) -> bool:
        ratios = [self._compute_roi_ratio(depth, roi) for roi in self.rois]
        ratio = min(ratios)
        self.history.append(ratio)
        if len(self.history) > self.window:
            self.history.pop(0)
        smoothed = sum(self.history) / len(self.history)
        return smoothed >= self.threshold
