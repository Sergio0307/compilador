import unittest
from dataclasses import FrozenInstanceError

from world.entities import ObjectType, Terrain, TerrainType, WorldObject


class TestDefinitions(unittest.TestCase):
    def test_terrain_definition_keeps_the_file_values(self):
        grass = TerrainType(name="Grass", char=".", resource_max=100, regen=2)

        self.assertEqual(grass.name, "Grass")
        self.assertEqual(grass.char, ".")
        self.assertEqual(grass.resource_max, 100)
        self.assertEqual(grass.regen, 2)

    def test_object_definition_keeps_the_file_values(self):
        rock = ObjectType(name="Rock", char="#", resource_max=100)

        self.assertEqual(rock.name, "Rock")
        self.assertEqual(rock.char, "#")
        self.assertEqual(rock.resource_max, 100)

    def test_definitions_are_immutable(self):
        grass = TerrainType(name="Grass", char=".", resource_max=100, regen=2)

        with self.assertRaises(FrozenInstanceError):
            grass.regen = 3

    def test_terrain_starts_with_a_full_reserve(self):
        grass = Terrain(TerrainType("Grass", ".", 100, 2))

        self.assertEqual(grass.reserve, 100)
        self.assertEqual(grass.resource_max, 100)

    def test_terrain_damage_floors_at_zero_and_never_destroys_it(self):
        grass = Terrain(TerrainType("Grass", ".", 100, 2))

        self.assertFalse(grass.damage(150))
        self.assertEqual(grass.reserve, 0)
        self.assertFalse(grass.damage(1))
        self.assertEqual(grass.reserve, 0)

    def test_terrain_regenerates_without_passing_its_maximum(self):
        grass = Terrain(TerrainType("Grass", ".", 100, 2))

        grass.damage(99)
        self.assertEqual(grass.reserve, 1)

        grass.regenerate()
        self.assertEqual(grass.reserve, 3)

        for _ in range(60):
            grass.regenerate()
        self.assertEqual(grass.reserve, 100)

    def test_object_starts_full_and_disappears_at_zero(self):
        rock = WorldObject(ObjectType("Rock", "#", 100))

        self.assertEqual(rock.reserve, 100)
        self.assertFalse(rock.damage(60))
        self.assertEqual(rock.reserve, 40)
        self.assertTrue(rock.damage(40))
        self.assertEqual(rock.reserve, 0)
        self.assertTrue(rock.damage(10))


if __name__ == "__main__":
    unittest.main()
