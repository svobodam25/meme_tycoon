import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from game_state import GameState, MAX_PLOT_LEVEL
from main import Game
from world import HOME_ROW_STEP, World


class HomeDisplayTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_each_capacity_slot_has_distinct_position_clear_of_path_and_workshop(self):
        previous=None
        for level in range(MAX_PLOT_LEVEL+1):
            w=World(level)
            positions=[w.home_position(slot) for slot in range(w.capacity)]
            self.assertEqual(len(set(positions)),w.capacity)
            if previous:
                self.assertGreater(w.home.width,previous.width)
                self.assertGreater(w.home.height,previous.height)
            previous=w.home.copy()
            for x,y in positions:
                sprite_and_label=pygame.Rect(x-55,y-80,110,137)
                self.assertTrue(w.home.contains(sprite_and_label))
                self.assertFalse(w.workshop.colliderect(sprite_and_label))
                self.assertGreaterEqual(abs(x-640),96)
            for i,a in enumerate(positions):
                for b in positions[i+1:]:
                    self.assertTrue(abs(a[0]-b[0])>=124 or abs(a[1]-b[1])>=HOME_ROW_STEP)

    def test_full_plot_can_be_walked_and_every_individual_is_visible(self):
        w=World(MAX_PLOT_LEVEL)
        s=GameState(plot_level=MAX_PLOT_LEVEL)
        s.owned[0]=s.capacity
        s.levels[0]=list(range(1,s.capacity+1))
        seen=set()
        for slot in range(0,s.capacity,4):
            _,y=w.home_position(slot)
            w.camera=max(0,min(w.height-820,y-440))
            for species,unit,x,y in w.home_units(s):
                seen.add((species,unit))
            self.assertFalse(w.blocked(pygame.Vector2(640,y),s))
        self.assertEqual(seen,{(0,i) for i in range(56)})
        self.assertGreater(w.height,7100)

    def test_level_labels_render_per_piece_and_sale_removes_one_actor(self):
        with tempfile.TemporaryDirectory() as directory:
            g=Game(Path(directory)/"save.json",smoke=True)
            for _ in range(3):
                g.state.capture(0);g.state.deposit()
            g.state.levels[0]=[1,7,3]
            with patch.object(g,"text",wraps=g.text) as text:
                g.draw()
                labels={call.args[0] for call in text.call_args_list}
            self.assertTrue({"#1 · Lv 1","#2 · Lv 7","#3 · Lv 3"}.issubset(labels))
            self.assertFalse(any(str(label).startswith("×") for label in labels))
            g.state.sell(0,1)
            actors=list(g.world.home_units(g.state))
            self.assertEqual(len(actors),2)
            self.assertEqual(g.state.levels[0],[1,3])

    def test_legacy_capacity_has_room_without_allocating_a_giant_background(self):
        w=World(base_slots=10008)
        s=GameState(base_slots=10008)
        s.owned[0]=10001
        s.levels[0]=[1]*10001
        _,last_y=w.home_position(10000)
        w.camera=last_y-440
        actors=list(w.home_units(s))
        self.assertIn(10000,[unit for species,unit,x,y in actors])
        self.assertLess(len(actors),40)
        self.assertEqual(w.background.get_height(),7100)
        self.assertTrue(w.home.collidepoint(w.home_position(10000)))
