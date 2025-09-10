"""Capture pipeline saving synchronized images."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class CapturePipeline:
    def __init__(self, output_root: Path):
        self.output_root = output_root

    def _build_path(self, ts: datetime, cam_name: str, result: str) -> Path:
        root = self.output_root / ts.strftime("%Y/%m/%d")
        root.mkdir(parents=True, exist_ok=True)
        filename = ts.strftime("%Y_%m%d_%H%M%S") + f"_{cam_name}_{result}.jpg"
        return root / filename

    def capture(self, frames: Dict[str, object], result: str, ts: datetime | None = None) -> List[Path]:
        ts = ts or datetime.now()
        saved: List[Path] = []
        for cam_name in frames:
            path = self._build_path(ts, cam_name, result)
            with path.open("wb") as f:
                f.write(b"")
            saved.append(path)
        return saved
