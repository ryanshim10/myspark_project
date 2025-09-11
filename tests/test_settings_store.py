from pathlib import Path
from app.services.settings_store import SettingsStore


def test_settings_store(tmp_path):
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save({"a": 1})
    assert store.load()["a"] == 1
