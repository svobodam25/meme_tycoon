import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import json
from pathlib import Path
import tempfile
import unittest

import pygame

from game_state import GameState
from main import Game
from world import CAPTURE_TIME, HOME, SPAWN, OFFSET, GATES


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.game = Game(Path(self.directory.name)/"save.json", smoke=True)

    def tearDown(self):
        pygame.quit()
        self.directory.cleanup()

    def advance(self, seconds, direction=(0, 0), holding=False):
        for _ in range(round(seconds/.02)):
            self.game.world.update(.02, direction, holding, self.game)

    def test_walk_north_camera_and_home_only_menu(self):
        g = self.game
        self.assertEqual(g.view, "world")
        self.assertTrue(g.world.at_home)
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, mod=0))
        self.assertEqual(g.view, "menu")
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        self.advance(2, (0, -1))
        self.assertFalse(g.world.at_home)
        self.assertLess(g.world.player.y, SPAWN[1])
        g.world.interact(g)
        self.assertEqual(g.view, "world")
        g.draw()
        self.assertAlmostEqual(g.world.camera, g.world.player.y-440)

    def test_capture_requires_hold_and_return_home(self):
        g = self.game
        g.world.player.update(g.world.encounters[0]["pos"])
        self.advance(.6, holding=True)
        self.assertIsNone(g.state.cargo)
        self.advance(.02, holding=False)
        self.assertEqual(g.world.progress, 0)
        self.advance(CAPTURE_TIME+.1, holding=True)
        self.assertEqual(g.state.cargo, 0)
        self.assertEqual(g.state.income, 0)
        self.assertGreater(g.world.encounters[0]["cooldown"], 0)
        self.assertFalse(g.state.capture(1))
        loaded, _ = GameState.load(g.path)
        self.assertEqual(loaded.cargo, 0)
        g.world.player.update(SPAWN)
        self.advance(.02)
        self.assertIsNone(g.state.cargo)
        self.assertEqual(g.state.owned[0], 1)
        self.assertEqual(g.state.income, 1)
        loaded, _ = GameState.load(g.path)
        self.assertEqual(loaded.owned[0], 1)
        self.assertIsNone(loaded.cargo)

    def test_capture_out_of_range_and_moving_interrupts(self):
        g = self.game
        self.advance(2, holding=True)
        self.assertIsNone(g.state.cargo)
        g.world.player.update(g.world.encounters[0]["pos"])
        self.advance(.6, holding=True)
        self.advance(.02, (1,0), holding=True)
        self.assertEqual(g.world.progress, 0)
        g.world.player.update(640, 2300+OFFSET)
        self.advance(2, holding=True)
        self.assertIsNone(g.state.cargo)

    def test_gate_cost_blocks_and_then_allows_walking(self):
        g = self.game
        g.world.player.update(640, 1700+OFFSET)
        self.advance(1, (0,-1))
        self.assertGreaterEqual(g.world.player.y, 1673+OFFSET)
        g.world.interact(g)
        self.assertEqual(g.state.location, 0)
        g.state.coins = 3500
        g.world.interact(g)
        self.assertEqual(g.state.location, 1)
        self.assertEqual(g.state.coins, 0)
        self.advance(1, (0,-1))
        self.assertLess(g.world.player.y, 1650+OFFSET)
        self.assertEqual(g.world.region, 1)
        self.assertFalse(g.state.capture(4))

    def test_fence_house_and_world_boundaries(self):
        g = self.game
        g.world.player.update(290, 2660+OFFSET)
        self.advance(2, (-1,0))
        self.assertGreater(g.world.player.x, HOME.left)
        g.world.player.update(880, 2760+OFFSET)
        self.advance(1, (0,1))
        self.assertLess(g.world.player.y, 2790+OFFSET)
        g.world.player.update(640, 2450+OFFSET)
        self.advance(1, (0,1))
        self.assertTrue(g.world.at_home)

    def test_all_regions_render_and_prestige_returns_home(self):
        g = self.game
        g.state.location = 7
        for y in [SPAWN[1]]+[2040+OFFSET-zone*800 for zone in range(8)]:
            g.world.player.update(640,y)
            g.draw()
        g.state.gain(1_000_000)
        g.state.capture(4)
        g.ascend()
        self.assertEqual(tuple(g.world.player), SPAWN)
        self.assertIsNone(g.state.cargo)
        self.assertEqual(g.state.location, 0)

    def test_old_saves_load_without_cargo_and_bad_cargo_is_rejected(self):
        g = self.game
        g.state.save(g.path)
        data = json.loads(g.path.read_text())
        del data["cargo"]
        g.path.write_text(json.dumps(data))
        loaded, _ = GameState.load(g.path)
        self.assertIsNone(loaded.cargo)
        for value in (-1, 6, False, "0", 4):
            data["cargo"] = value
            g.path.write_text(json.dumps(data))
            with self.subTest(cargo=value), self.assertRaises(ValueError):
                GameState.load(g.path)

    def test_each_new_gate_is_walkable_after_unlock(self):
        g=self.game
        g.state.coins=1e15
        for y,level in GATES:
            g.world.player.update(640,y+50)
            self.advance(.4,(0,-1))
            self.assertGreaterEqual(g.world.player.y,y+23)
            g.world.interact(g)
            self.assertEqual(g.state.location,level)
            self.advance(.4,(0,-1))
            self.assertLess(g.world.player.y,y)
