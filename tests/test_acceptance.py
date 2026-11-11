"""Acceptance checks for the base project.

Run from the repository root:

    python -m unittest tests.test_acceptance -v

The UI check uses SDL's dummy video driver so it also works headlessly.
"""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from lang.compiler import compile_species  # noqa: E402
from loaders.resource_manager import ResourceManager  # noqa: E402
from ui.app import InstinctApp  # noqa: E402
from world.map import WorldMap  # noqa: E402
from world.world import World  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
ANNEX = ROOT / "examples" / "annex"


class BaseAcceptance(unittest.TestCase):
    def test_content_loads_without_errors(self):
        manager = ResourceManager(ROOT)
        errors = manager.load_all()

        self.assertEqual(errors, [])
        self.assertIn("Rift of the Ancients", manager.maps)
        self.assertEqual(manager.maps["Rift of the Ancients"].width, 40)
        self.assertEqual(manager.maps["Rift of the Ancients"].height, 20)
        for name in ("Uruk", "DireCreep", "RadiantCreep", "Roshan"):
            self.assertIn(name, manager.creatures)

        rift = manager.maps["Rift of the Ancients"].build()
        self.assertEqual(rift.name, "Rift of the Ancients")
        self.assertEqual(rift.width, 40)
        self.assertEqual(rift.height, 20)

    def test_annex_examples_compile_and_run(self):
        examples = sorted(ANNEX.glob("*.ins"))
        self.assertEqual(len(examples), 4, examples)

        world = World(WorldMap.blank(24, 12), seed=7)
        for path in examples:
            species = compile_species(path.read_text(encoding="utf-8"), str(path))
            x, y = world.free_cells()[0]
            world.add_creature(species, x, y)

        for _ in range(2):
            world.run_round()

        self.assertEqual(world.tick, 2)

    def test_ui_preparation_to_play_and_restart(self):
        app = InstinctApp(ROOT)
        try:
            self.assertEqual(app.load_errors, [])
            self.assertEqual(app.phase, "preparation")
            self.assertIsNotNone(app.selected_map)
            self.assertIsNotNone(app.world)

            names = list(app.manager.creatures)
            app.selected_species_index = names.index("Uruk")
            x, y = app.world_map.free_cells()[0]
            cell_size, left, top = app.map_view._layout(app.world_map, app.MAP_RECT)
            position = (
                left + x * cell_size + cell_size // 2,
                top + y * cell_size + cell_size // 2,
            )
            app.place_creature(position)
            self.assertEqual(len(app.world.creatures), 1)

            app.start_game()
            self.assertEqual(app.phase, "playing")
            self.assertFalse(app.paused)

            app.update(0.6)
            self.assertGreaterEqual(app.world.tick, 1)

            app.handle_event(
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
            )
            self.assertTrue(app.paused)
            tick_before_step = app.world.tick
            app.step_once()
            self.assertEqual(app.world.tick, tick_before_step + 1)

            app.set_speed(2)
            self.assertEqual(app.ticks_per_second, 30)

            app.restart_game()
            self.assertEqual(app.phase, "preparation")
            self.assertEqual(app.world.tick, 0)
            self.assertEqual(app.world.creatures, [])
            self.assertEqual(app.ticks_per_second, 2)

            app.draw()
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
