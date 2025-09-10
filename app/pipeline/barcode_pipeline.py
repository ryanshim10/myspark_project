"""Barcode processing pipeline (stub)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


def _decode(img) -> List[str]:  # pragma: no cover - default decoder
    return []


@dataclass
class BarcodeResult:
    text: Optional[str]
    crop_path: Optional[Path]


class BarcodePipeline:
    """Performs rotation sweep and decoding."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(self, img, prefix: str) -> BarcodeResult:
        cropped_path = self.output_dir / f"{prefix}_BARCODE.jpg"
        with cropped_path.open("wb") as f:
            f.write(b"")
        decoded = _decode(img)
        text = decoded[0] if decoded else None
        return BarcodeResult(text=text, crop_path=cropped_path)
