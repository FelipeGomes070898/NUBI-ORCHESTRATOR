import tempfile
import unittest
from pathlib import Path
from nubi.render import render, probe
from nubi import director

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

    def test_estilos_camadas(self):
        for estilo in ("parallax", "cartoon", "3d"):
            with self.subTest(estilo=estilo), tempfile.TemporaryDirectory() as folder:
                events = []
                p = render("Teste", "The universe began.\nA quiet forest at night.", "en", 8, False, 360, folder,
                           style=estilo, cb=lambda *a: events.append(a[0]))
                self.assertTrue((p/"video.mp4").exists() and (p/"miniatura.jpg").exists())
                self.assertIn("pronto", events)

    def test_diretor(self):
        plano = director.plan(["The universe began.", "Um dia de sol."])
        self.assertEqual([c["humor"] for c in plano], ["espaco", "dia"])
