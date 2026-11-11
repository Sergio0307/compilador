"""Tests for the Dota-themed content added to the repository."""

import unittest

from loaders.resource_manager import ResourceManager


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


if __name__ == "__main__":
    unittest.main()
