"""Settings persistence using JSON."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.save({})

    def load(self) -> Dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
