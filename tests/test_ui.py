"""Headless rendering and input integration checks."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame
from main import Game
from game_state import LOCATIONS


class InterfaceTests(unittest.TestCase):
    def test_menu_upgrades_only_selected_individual(self):
        with tempfile.TemporaryDirectory() as directory:
            game=Game(Path(directory)/"save.json",smoke=True)
            try:
                for _ in range(2):
                    game.state.capture(0)
                    game.state.deposit()
                game.world.interact(game)
                game.location=0
                game.draw()
                game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e,mod=0))
                with patch.object(game,"mouse",return_value=(230,300)):
                    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1))
                self.assertEqual(game.inventory.selected,(0,1))
                game.draw()
                with patch.object(game,"mouse",return_value=(1000,685)):
                    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1))
                self.assertEqual(game.state.levels[0],[1,2])
                self.assertEqual(game.state.coins,25)
                self.assertEqual(game.state.owned[0],2)
                self.assertFalse(hasattr(game,"buy"))
            finally:
                pygame.quit()

    def test_screens_actions_and_resize(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Game(Path(directory)/"save.json", smoke=True)
            try:
                game.world.interact(game)
                self.assertEqual(game.view, "menu")
                game.state.capture(0)
                game.state.deposit()
                game.draw()
                with patch.object(game, "mouse", return_value=(1000, 685)):
                    action = next(action for rect, action in game.buttons if rect.collidepoint(game.mouse()))
                    action()
                self.assertEqual(game.state.owned[0], 1)
                self.assertEqual(game.state.levels[0], [2])
                game.state.gain(4_000_000)
                game.state.coins=1e15
                for _ in range(7):
                    game.unlock()
                for location in range(len(LOCATIONS)):
                    game.location = location
                    for tab in ("Inventář", "Úspěchy", "Prestige"):
                        game.tab = tab
                        game.draw()
                game.modal = True
                game.draw()
                self.assertEqual(len(game.buttons), 2)
                game.ascend()
                self.assertEqual(game.state.prestige, 2)
                self.assertTrue(game.path.exists())
                game.window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
                game.draw()
                self.assertGreater(game.viewport()[0], 0)
            finally:
                pygame.quit()

    def test_unreadable_save_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"save.json"
            path.write_text("broken")
            game = Game(path, smoke=True)
            try:
                self.assertFalse(game.save_enabled)
                game.save()
                self.assertEqual(path.read_text(), "broken")
                game.draw()
            finally:
                pygame.quit()
