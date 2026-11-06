"""Tests del cargador de mapas `.map`.

Se ejecutan desde la raíz del repositorio con:

    python -m unittest loaders.test_map_loader -v
"""

import tempfile
import unittest
from pathlib import Path

from loaders.resource_manager import ResourceManager
from world.map import MapDef, WorldMap


class TestMapLoader(unittest.TestCase):
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
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_base(self):
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
            "char #\n"
            "resource_max 100\n",
        )

    def test_valid_map_is_a_blueprint_and_builds_fresh_cells(self):
        self.write_base()
        self.write(
            "maps/test.map",
            "Test Field\n"
            "....\n"
            ".#..\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(errors, [])
        map_def = self.manager.maps["Test Field"]
        self.assertIsInstance(map_def, MapDef)
        self.assertEqual(map_def.width, 4)
        self.assertEqual(map_def.height, 2)

        world_map = map_def.build()
        self.assertIsInstance(world_map, WorldMap)
        self.assertEqual(world_map.name, "Test Field")
        self.assertEqual(world_map.terrain_at(0, 0).name, "Grass")
        self.assertEqual(world_map.object_at(1, 1).name, "Rock")
        self.assertEqual(world_map.terrain_at(1, 1).name, "Grass")
        self.assertEqual(world_map.terrain_at(1, 1).reserve, 100)
        self.assertEqual(world_map.object_at(1, 1).reserve, 100)

    def test_unknown_char_rejects_only_that_map(self):
        self.write_base()
        self.write(
            "maps/bad.map",
            "Bad\n"
            "..\n"
            ".?\n",
        )
        self.write(
            "maps/good.map",
            "Good\n"
            "..\n"
            "..\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 3)
        self.assertIn("carácter desconocido '?'", errors[0].message)
        self.assertIn("bad.map", errors[0].path)
        self.assertIn("Good", self.manager.maps)
        self.assertNotIn("Bad", self.manager.maps)

    def test_ragged_rows_reject_the_map(self):
        self.write_base()
        self.write(
            "maps/bad.map",
            "Ragged\n"
            "...\n"
            "..\n",
        )

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("se esperaba 3", errors[0].message)
        self.assertNotIn("Ragged", self.manager.maps)

    def test_map_without_rows_is_rejected(self):
        self.write_base()
        self.write("maps/empty.map", "Empty\n")

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("no tiene filas", errors[0].message)
        self.assertNotIn("Empty", self.manager.maps)

    def test_object_char_is_placed_on_first_declared_terrain(self):
        self.write(
            "terrains/grass.te",
            "terrain Grass\n"
            "char .\n"
            "resource_max 100\n"
            "regen 2\n",
        )
        self.write(
            "terrains/sand.te",
            "terrain Sand\n"
            "char ,\n"
            "resource_max 30\n"
            "regen 0\n",
        )
        self.write(
            "objects/rock.ob",
            "object Rock\n"
            "char #\n"
            "resource_max 100\n",
        )
        self.write("maps/objects.map", "Objects\n#\n")

        errors = self.manager.load_all()

        self.assertEqual(errors, [])
        world_map = self.manager.maps["Objects"].build()
        self.assertEqual(world_map.terrain_at(0, 0).name, "Grass")
        self.assertEqual(world_map.object_at(0, 0).name, "Rock")

    def test_building_twice_gives_independent_reserves(self):
        self.write_base()
        self.write("maps/fresh.map", "Fresh\n.\n#\n")

        self.manager.load_all()
        map_def = self.manager.maps["Fresh"]

        first = map_def.build()
        first.terrain_at(0, 0).damage(99)
        first.object_at(0, 1).damage(100)

        second = map_def.build()

        self.assertEqual(first.terrain_at(0, 0).reserve, 1)
        self.assertEqual(first.object_at(0, 1).reserve, 0)
        self.assertEqual(second.terrain_at(0, 0).reserve, 100)
        self.assertEqual(second.object_at(0, 1).reserve, 100)

    def test_duplicate_map_name_is_rejected(self):
        self.write_base()
        self.write("maps/a.map", "Same\n..\n")
        self.write("maps/b.map", "Same\n..\n")

        errors = self.manager.load_all()

        self.assertEqual(len(errors), 1)
        self.assertIn("mapa duplicado 'Same'", errors[0].message)
        self.assertEqual(len(self.manager.maps), 1)


if __name__ == "__main__":
    unittest.main()
