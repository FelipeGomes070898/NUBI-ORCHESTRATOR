import tempfile
import unittest
from pathlib import Path
from nubi.render import render, probe

class TesteCPU(unittest.TestCase):
    def test_video_vertical(self):
        with tempfile.TemporaryDirectory() as folder:
            args = ("Teste", "Hello there.\nHere comes the sun.", "en", 8, True, 360, folder)
            project = render(*args)
            video = probe(project/"video.mp4")["streams"][0]
            self.assertEqual((video["width"],video["height"]),(360,640))
            clip = project/"cena-01.mp4"
            modified = clip.stat().st_mtime_ns
            self.assertEqual(render(*args),project)
            self.assertEqual(clip.stat().st_mtime_ns,modified)
            self.assertTrue((Path(folder)/"catalogo.sqlite").exists())
