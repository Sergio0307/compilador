"""Tests for the Dota-themed content added to the repository."""

import unittest

from loaders.resource_manager import ResourceManager
from world.world import World


class TestDotaContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = ResourceManager(".")
        cls.errors = cls.manager.load_all()

    def test_all_content_loads_without_errors(self):
        self.assertEqual([str(e) for e in self.errors], [])

    def test_dota_factions_are_available(self):
        self.assertEqual(self.manager.creatures["RadiantCreep"].faction, "radiant")
        self.assertEqual(self.manager.creatures["DireCreep"].faction, "dire")
        self.assertEqual(self.manager.creatures["Roshan"].faction, "neutral")

    def test_rift_map_has_dota_terrain_and_objects(self):
        map_def = self.manager.maps["Rift of the Ancients"]
        self.assertEqual((map_def.width, map_def.height), (40, 20))

        rift = map_def.build()
        self.assertEqual(rift.name, "Rift of the Ancients")
        self.assertEqual(rift.terrain_at(18, 9).name, "River")
        self.assertEqual(rift.terrain_at(33, 3).name, "HighGround")
        self.assertEqual(rift.object_at(3, 3).name, "Tree")

    def test_roshan_keeps_his_boss_stats(self):
        roshan = self.manager.creatures["Roshan"]
        self.assertEqual(
            (roshan.health, roshan.vision, roshan.lifespan),
            (600, 5, 9999),
        )

    def test_creep_remembers_and_uses_its_lane_anchor(self):
        world = World(self.manager.maps["Test Field"].build(), seed=1)
        dire = world.add_creature(self.manager.creatures["DireCreep"], 2, 2)

        world.run_round()
        self.assertEqual(dire.execution.variables["lane_x"], 2)
        self.assertEqual(dire.execution.variables["lane_y"], 2)

        # Move it away by hand; the next patrol step should head back west.
        world.map.move_creature(dire, 7, 4)
        world.run_round()
        self.assertEqual((dire.x, dire.y), (6, 4))
        self.assertEqual(dire.execution.variables["lane_x"], 2)
        self.assertEqual(dire.execution.variables["lane_y"], 2)


if __name__ == "__main__":
    unittest.main()
