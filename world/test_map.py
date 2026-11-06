"""Tests de casillas y del mapa.

Se ejecutan desde la raíz del repositorio con:

    python -m unittest world.test_map -v
"""

import unittest
from types import SimpleNamespace

from lang.catalog import CONSTANTS
from world.entities import ObjectType, Terrain, TerrainType, WorldObject
from world.map import Cell, WorldMap

GRASS = TerrainType("Grass", ".", 100, 2)
ROCK = ObjectType("Rock", "#", 100)


def make_creature(species, faction, x, y, vision=5):
    """Sustituto mínimo de Creature para probar el mapa sin el intérprete."""
    return SimpleNamespace(
        species=species,
        faction=faction,
        x=x,
        y=y,
        vision=vision,
    )


class TestCell(unittest.TestCase):
    def test_cell_rejects_object_and_creature_together(self):
        with self.assertRaises(ValueError):
            Cell(
                Terrain(GRASS),
                obj=WorldObject(ROCK),
                creature=SimpleNamespace(x=0, y=0),
            )


class TestWorldMap(unittest.TestCase):
    def test_blank_map_has_independent_cells_with_full_reserve(self):
        world_map = WorldMap.blank(3, 2, GRASS)

        self.assertEqual(world_map.width, 3)
        self.assertEqual(world_map.height, 2)
        self.assertEqual(len(world_map.free_cells()), 6)
        self.assertEqual(world_map.terrain_at(0, 0).name, "Grass")
        self.assertEqual(world_map.terrain_at(0, 0).reserve, 100)
        self.assertIsNot(
            world_map.cell_at(0, 0).terrain,
            world_map.cell_at(1, 0).terrain,
        )

    def test_blank_map_accepts_another_terrain_definition(self):
        sand = TerrainType("Sand", "s", 10, 0)
        world_map = WorldMap.blank(2, 1, sand)

        self.assertEqual(world_map.terrain_at(1, 0).name, "Sand")
        self.assertEqual(world_map.terrain_at(1, 0).reserve, 10)

    def test_out_of_bounds_has_no_cell(self):
        world_map = WorldMap.blank(3, 2, GRASS)

        self.assertFalse(world_map.in_bounds(-1, 0))
        self.assertFalse(world_map.in_bounds(3, 0))
        self.assertIsNone(world_map.cell_at(3, 0))
        self.assertIsNone(world_map.terrain_at(3, 0))
        self.assertFalse(world_map.is_walkable(3, 0))

    def test_object_blocks_a_cell(self):
        world_map = WorldMap.blank(3, 2, GRASS)
        rock = WorldObject(ROCK)

        self.assertTrue(world_map.place_object(rock, 1, 1))
        self.assertIs(world_map.object_at(1, 1), rock)
        self.assertFalse(world_map.is_walkable(1, 1))
        self.assertNotIn((1, 1), world_map.free_cells())

        self.assertFalse(world_map.place_object(WorldObject(ROCK), 1, 1))
        self.assertFalse(world_map.place_object(WorldObject(ROCK), 3, 0))

    def test_creature_blocks_a_cell_and_gets_coordinates(self):
        world_map = WorldMap.blank(3, 2, GRASS)
        creature = SimpleNamespace(x=0, y=0)

        self.assertTrue(world_map.place_creature(creature, 0, 1))
        self.assertEqual((creature.x, creature.y), (0, 1))
        self.assertIs(world_map.creature_at(0, 1), creature)
        self.assertFalse(world_map.is_walkable(0, 1))

        other = SimpleNamespace(x=0, y=0)
        self.assertFalse(world_map.place_creature(other, 0, 1))
        self.assertFalse(world_map.place_creature(other, 3, 0))

    def test_remove_creature_frees_the_cell(self):
        world_map = WorldMap.blank(2, 2, GRASS)
        creature = SimpleNamespace(x=0, y=0)
        world_map.place_creature(creature, 0, 0)

        self.assertTrue(world_map.remove_creature(creature))
        self.assertIsNone(world_map.creature_at(0, 0))
        self.assertTrue(world_map.is_walkable(0, 0))
        self.assertFalse(world_map.remove_creature(creature))

    def test_move_creature_updates_both_cells_and_coordinates(self):
        world_map = WorldMap.blank(3, 3, GRASS)
        creature = SimpleNamespace(x=0, y=0)
        world_map.place_creature(creature, 0, 0)

        self.assertTrue(world_map.move_creature(creature, 2, 1))
        self.assertIsNone(world_map.creature_at(0, 0))
        self.assertIs(world_map.creature_at(2, 1), creature)
        self.assertEqual((creature.x, creature.y), (2, 1))

    def test_move_creature_is_blocked_by_objects_creatures_and_borders(self):
        world_map = WorldMap.blank(3, 3, GRASS)
        creature = SimpleNamespace(x=0, y=0)
        world_map.place_creature(creature, 0, 0)
        world_map.place_object(WorldObject(ROCK), 1, 0)

        self.assertFalse(world_map.move_creature(creature, 1, 0))
        self.assertFalse(world_map.move_creature(creature, 3, 0))
        self.assertEqual((creature.x, creature.y), (0, 0))

        other = SimpleNamespace(x=0, y=0)
        world_map.place_creature(other, 0, 1)
        self.assertFalse(world_map.move_creature(creature, 0, 1))
        self.assertEqual((creature.x, creature.y), (0, 0))

    def test_free_cells_excludes_objects_and_creatures(self):
        world_map = WorldMap.blank(2, 2, GRASS)
        world_map.place_object(WorldObject(ROCK), 0, 0)
        world_map.place_creature(SimpleNamespace(x=0, y=0), 1, 1)

        self.assertEqual(world_map.free_cells(), [(1, 0), (0, 1)])

    def test_map_rejects_empty_or_ragged_grids(self):
        with self.assertRaises(ValueError):
            WorldMap("empty", [])
        with self.assertRaises(ValueError):
            WorldMap("ragged", [[Cell(Terrain(GRASS))], []])
        with self.assertRaises(ValueError):
            WorldMap.blank(0, 1, GRASS)


class TestVision(unittest.TestCase):
    def setUp(self):
        self.world_map = WorldMap.blank(7, 7, GRASS)
        self.viewer = make_creature("Viewer", "a", 3, 3)
        self.ally = make_creature("Ally", "a", 4, 3)
        self.enemy = make_creature("Enemy", "b", 5, 3)
        self.rock = WorldObject(ROCK)

        self.world_map.place_creature(self.viewer, 3, 3)
        self.world_map.place_creature(self.ally, 4, 3)
        self.world_map.place_creature(self.enemy, 5, 3)
        self.world_map.place_object(self.rock, 3, 4)

    def test_see_own_cell_is_ally(self):
        self.assertEqual(
            self.world_map.see(self.viewer, 3, 3),
            CONSTANTS["ALLY"],
        )

    def test_see_faction_and_ground(self):
        self.assertEqual(
            self.world_map.see(self.viewer, 4, 3),
            CONSTANTS["ALLY"],
        )
        self.assertEqual(
            self.world_map.see(self.viewer, 5, 3),
            CONSTANTS["ENEMY"],
        )
        self.assertEqual(
            self.world_map.see(self.viewer, 2, 2),
            CONSTANTS["GROUND"],
        )

    def test_see_object(self):
        self.assertEqual(
            self.world_map.see(self.viewer, 3, 4),
            CONSTANTS["OBJECT"],
        )

    def test_see_outside_vision_is_none(self):
        self.assertEqual(
            self.world_map.see(self.viewer, 9, 3),
            CONSTANTS["NONE"],
        )

    def test_see_border_within_vision_is_object(self):
        self.assertEqual(
            self.world_map.see(self.viewer, -1, 3),
            CONSTANTS["OBJECT"],
        )

    def test_see_at_exact_vision_edge_is_visible(self):
        self.assertEqual(
            self.world_map.see(self.viewer, 8, 3),
            CONSTANTS["OBJECT"],
        )

    def test_vision_is_checked_before_border(self):
        near = make_creature("Near", "a", 3, 3, vision=3)

        self.assertEqual(
            self.world_map.see(near, -1, 3),
            CONSTANTS["NONE"],
        )

    def test_name_at_uses_species_object_and_terrain(self):
        self.assertEqual(self.world_map.name_at(self.viewer, 3, 3), "Viewer")
        self.assertEqual(self.world_map.name_at(self.viewer, 4, 3), "Ally")
        self.assertEqual(self.world_map.name_at(self.viewer, 5, 3), "Enemy")
        self.assertEqual(self.world_map.name_at(self.viewer, 3, 4), "Rock")
        self.assertEqual(self.world_map.name_at(self.viewer, 2, 2), "Grass")

    def test_name_at_outside_vision_or_map_is_empty(self):
        self.assertEqual(self.world_map.name_at(self.viewer, 9, 3), "")
        self.assertEqual(self.world_map.name_at(self.viewer, -1, 3), "")


if __name__ == "__main__":
    unittest.main()
