import tempfile
import unittest
from pathlib import Path

from periflow.config import SettingsStore
from periflow.models import AppSettings


class SettingsStoreTests(unittest.TestCase):
    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = SettingsStore(base_dir=Path(tmp_dir))
            settings = AppSettings(
                server_port=6000,
                audio_port=6001,
                resolution="1080p",
                fps=30,
                audio_transport="tcp",
            )
            store.save(settings)
            loaded = store.load()
            self.assertEqual(loaded.server_port, 6000)
            self.assertEqual(loaded.audio_port, 6001)
            self.assertEqual(loaded.resolution, "1080p")
            self.assertEqual(loaded.fps, 30)
            self.assertEqual(loaded.audio_transport, "tcp")


if __name__ == "__main__":
    unittest.main()
