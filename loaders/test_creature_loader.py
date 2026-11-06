"""Tests del cargador de criaturas `.ins`.

Se ejecutan desde la raíz del repositorio con:

    python -m unittest loaders.test_creature_loader -v
"""

import tempfile
import unittest
from pathlib import Path

from loaders.resource_manager import ResourceManager


VALID_URUK = """\
creature Uruk
faction isengard
health 80
vision 6
lifespan 400
start:
    say("hi")
    wait(1)
    goto start
"""


class TestCreatureLoader(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for directory in ("terrains", "objects", "maps", "creatures"):
            (self.root / directory).mkdir()
        self.manager = ResourceManager(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_creature_is_compiled(self):
        self.write("creatures/uruk.ins", VALID_URUK)

        errors = self.manager.load_all()

        self.assertEqual(errors, [])
        uruk = self.manager.creatures["Uruk"]
        self.assertEqual(uruk.name, "Uruk")
        self.assertEqual(uruk.faction, "isengard")
        self.assertEqual(uruk.health, 80)
        self.assertEqual(uruk.vision, 6)
        self.assertEqual(uruk.lifespan, 400)

    def test_semantic_error_reports_line_and_keeps_other_creatures(self):
        self.write(
            "creatures/bad.ins",
            "creature Bad\n"
            "faction isengard\n"
            "health 0\n"
            "vision 6\n"
            "lifespan 400\n"
            "start:\n"
            "    wait(1)\n",
        )
        self.write("creatures/uruk.ins", VALID_URUK)

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 3)
        self.assertIn("health", errors[0].message)
        self.assertIn("bad.ins", errors[0].path)
        self.assertNotIn("Bad", self.manager.creatures)
        self.assertIn("Uruk", self.manager.creatures)

    def test_lexical_error_reports_line_and_skips_the_file(self):
        self.write(
            "creatures/broken.ins",
            "creature Broken\n"
            "faction isengard\n"
            "health 10\n"
            "vision 3\n"
            "lifespan 10\n"
            "start:\n"
            "    @\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 7)
        self.assertIn("broken.ins", errors[0].path)
        self.assertNotIn("Broken", self.manager.creatures)

    def test_duplicate_species_name_is_rejected(self):
        self.write("creatures/a.ins", VALID_URUK)
        self.write("creatures/b.ins", VALID_URUK)

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("especie duplicada 'Uruk'", errors[0].message)
        self.assertEqual(list(self.manager.creatures), ["Uruk"])


if __name__ == "__main__":
    unittest.main()
