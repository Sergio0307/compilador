"""Tests del cargador de terrenos y objetos.

Se ejecutan desde la raíz del repositorio con:

    python -m unittest loaders.test_resource_manager -v
"""

import tempfile
import unittest
from pathlib import Path

from loaders.resource_manager import LoadError, ResourceManager
from world.entities import ObjectType, TerrainType


class TestResourceManager(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "terrains").mkdir()
        (self.root / "objects").mkdir()
        (self.root / "maps").mkdir()
        (self.root / "creatures").mkdir()
        self.manager = ResourceManager(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_valid_terrain_and_object(self):
        self.write(
            "terrains/grass.te",
            "# ajustes base\n"
            "terrain Grass\n"
            "char .\n"
            "resource_max 100\n"
            "regen 2\n",
        )
        self.write(
            "objects/rock.ob",
            "object Rock\n"
            "char #\n"
            "resource_max 100\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(errors, [])
        self.assertEqual(
            self.manager.terrains["Grass"],
            TerrainType("Grass", ".", 100, 2),
        )
        self.assertEqual(
            self.manager.objects["Rock"],
            ObjectType("Rock", "#", 100),
        )
        self.assertEqual(self.manager.maps, {})
        self.assertEqual(self.manager.creatures, {})

    def test_missing_field_is_reported_and_file_is_ignored(self):
        self.write(
            "terrains/bad.te",
            "terrain Bad\n"
            "char B\n"
            "resource_max 10\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("bad.te", str(errors[0]))
        self.assertIn("regen", str(errors[0]))
        self.assertNotIn("Bad", self.manager.terrains)

    def test_char_must_be_exactly_one_character(self):
        self.write(
            "terrains/bad.te",
            "terrain Bad\n"
            "char AB\n"
            "resource_max 10\n"
            "regen 1\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("exactamente uno", str(errors[0]))
        self.assertNotIn("Bad", self.manager.terrains)

    def test_negative_resource_max_is_rejected(self):
        self.write(
            "terrains/bad.te",
            "terrain Bad\n"
            "char B\n"
            "resource_max -1\n"
            "regen 1\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("no puede ser negativo", str(errors[0]))
        self.assertNotIn("Bad", self.manager.terrains)

    def test_char_is_unique_across_terrains_and_objects(self):
        self.write(
            "terrains/grass.te",
            "terrain Grass\n"
            "char .\n"
            "resource_max 100\n"
            "regen 2\n",
        )
        self.write(
            "objects/rock.ob",
            "object Rock\n"
            "char .\n"
            "resource_max 100\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("ya usado", str(errors[0]))
        self.assertIn("Grass", errors[0].message)
        self.assertEqual(self.manager.objects, {})

    def test_unknown_key_rejects_the_file(self):
        self.write(
            "objects/bad.ob",
            "object Bad\n"
            "char B\n"
            "resource_max 10\n"
            "regen 1\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("clave desconocida 'regen'", str(errors[0]))
        self.assertNotIn("Bad", self.manager.objects)

    def test_duplicate_terrain_name_is_rejected(self):
        self.write(
            "terrains/one.te",
            "terrain Grass\n"
            "char .\n"
            "resource_max 100\n"
            "regen 2\n",
        )
        self.write(
            "terrains/two.te",
            "terrain Grass\n"
            "char ,\n"
            "resource_max 50\n"
            "regen 1\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("terreno duplicado 'Grass'", str(errors[0]))
        self.assertEqual(len(self.manager.terrains), 1)

    def test_error_formats_path_line_and_message(self):
        with_line = LoadError("grass.te", 4, "mensaje")
        without_line = LoadError("grass.te", None, "mensaje")

        self.assertEqual(str(with_line), "grass.te:4: mensaje")
        self.assertEqual(str(without_line), "grass.te: mensaje")


if __name__ == "__main__":
    unittest.main()
