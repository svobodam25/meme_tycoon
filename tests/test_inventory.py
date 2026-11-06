import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from game_state import BRAINROTS
from inventory import GRID
from main import Game
from sprites import render_character


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.game=Game(Path(self.directory.name)/"save.json",smoke=True)
        self.game.world.interact(self.game)

    def tearDown(self):
        pygame.quit()
        self.directory.cleanup()

    def click(self,position):
        with patch.object(self.game,"mouse",return_value=position):
            self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1))

    def test_empty_inventory_has_no_slots(self):
        g=self.game
        g.draw()
        self.assertIsNone(g.inventory.selected)
        self.assertFalse(any(rect.colliderect(GRID) for rect,action in g.buttons))

    def test_every_individual_visible_across_species_without_location_filter(self):
        g=self.game
        g.state.location=7
        for i in (0,0,2,15):
            g.state.capture(i);g.state.deposit()
        g.location=0
        g.draw()
        slots=[(rect,action) for rect,action in g.buttons if rect.colliderect(GRID)]
        self.assertEqual(len(slots),4)
        self.click(slots[-1][0].center)
        self.assertEqual(g.inventory.selected,(15,0))
        # A new catch of an earlier species must not change the selected individual.
        g.state.capture(0);g.state.deposit()
        g.draw()
        self.assertEqual(g.inventory.selected,(15,0))

    def test_large_inventory_scroll_end_select_upgrade_and_save(self):
        g=self.game
        g.state.owned[0]=10001
        g.state.levels[0]=[1]*10001
        g.state.base_slots=10008
        g.state.coins=1000
        g.draw()
        self.assertLessEqual(len(g.buttons),30)
        g.handle_event(pygame.event.Event(pygame.MOUSEWHEEL,y=-2,x=0))
        self.assertEqual(g.inventory.scroll,128)
        g.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_END,mod=0))
        g.draw()
        last_rect=next(rect for rect,action in g.buttons if rect.collidepoint((70,670)))
        self.click(last_rect.center)
        self.assertEqual(g.inventory.selected,(0,10000))
        g.draw()
        self.click((1000,685))
        self.assertEqual(g.state.levels[0][-1],2)
        self.assertEqual(g.state.levels[0][0],1)
        self.assertEqual(g.state.coins,925)
        g.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_HOME,mod=0))
        self.assertEqual(g.inventory.scroll,0)
        g.save()
        from game_state import GameState
        restored,_=GameState.load(g.path)
        self.assertEqual(restored.levels[0][-1],2)

    def test_modal_blocks_scrolling_and_clipped_slots_do_not_steal_clicks(self):
        g=self.game
        g.state.owned[0]=30
        g.state.levels[0]=[1]*30
        g.state.base_slots=32
        g.handle_event(pygame.event.Event(pygame.MOUSEWHEEL,y=-1,x=0))
        g.draw()
        selected=g.inventory.selected
        self.click((100,220))
        self.assertEqual(g.inventory.selected,selected)
        g.modal=True
        g.handle_event(pygame.event.Event(pygame.MOUSEWHEEL,y=-1,x=0))
        self.assertEqual(g.inventory.scroll,64)

    def test_keyboard_navigation_and_prestige_clear_inventory(self):
        g=self.game
        g.state.owned[0]=25
        g.state.levels[0]=[1]*25
        g.state.base_slots=32
        for _ in range(4):
            g.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_DOWN,mod=0))
        self.assertEqual(g.inventory.selected,(0,20))
        self.assertGreater(g.inventory.scroll,0)
        g.state.gain(1000000)
        g.ascend()
        g.draw()
        self.assertIsNone(g.inventory.selected)
        self.assertEqual(g.inventory.scroll,0)

    def test_all_sprites_have_transparent_padding_and_cache(self):
        for b in BRAINROTS:
            with self.subTest(shape=b.shape):
                sprite=render_character(b.shape,b.color,1.0)
                self.assertTrue(sprite.get_flags() & pygame.SRCALPHA)
                self.assertEqual(sprite.get_at((0,0)).a,0)
                self.assertGreater(sprite.get_bounding_rect().width,40)
                self.game.character(200,200,b.shape,b.color,.64)
                cache_size=len(self.game.sprite_cache)
                self.game.character(300,200,b.shape,b.color,.64)
                self.assertEqual(len(self.game.sprite_cache),cache_size)
