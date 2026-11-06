import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from game_state import GameState, MAX_PLOT_LEVEL
from main import Game
from world import World, SPAWN


def fill(state):
    for _ in range(state.capacity):
        assert state.capture(0)
        assert state.deposit()


class PlotTests(unittest.TestCase):
    def test_capacity_reserves_space_for_cargo_and_sale_frees_slot(self):
        s=GameState()
        self.assertEqual(s.capacity,8)
        fill(s)
        self.assertFalse(s.capture(0))
        s.levels[0][3]=4
        before=s.coins
        self.assertEqual(s.sell_price(0,3),50)
        self.assertTrue(s.sell(0,3))
        self.assertEqual(s.coins,before+50)
        self.assertEqual(s.owned[0],7)
        self.assertEqual(s.levels[0],[1]*7)
        self.assertEqual(s.income,7)
        self.assertEqual(s.run_earned,0)
        self.assertTrue(s.capture(0))
        self.assertEqual(s.used_slots,8)
        self.assertFalse(s.capture(1))
        self.assertTrue(s.deposit())
        self.assertEqual(s.used_slots,8)
        self.assertFalse(s.capture(0))
        self.assertFalse(s.sell(0,99))
        self.assertFalse(s.sell(-1,0))

    def test_expansion_cost_limits_save_and_prestige(self):
        s=GameState()
        self.assertFalse(s.expand_plot())
        self.assertEqual(s.coins,100)
        s.coins=1e10
        for level in range(MAX_PLOT_LEVEL):
            cost=1000*4**level
            self.assertEqual(s.expansion_price,cost)
            before=s.coins
            self.assertTrue(s.expand_plot())
            self.assertEqual(s.coins,before-cost)
            self.assertEqual(s.capacity,8+(level+1)*8)
        self.assertFalse(s.expand_plot())
        s.gain(1e6)
        self.assertTrue(s.ascend())
        self.assertEqual(s.capacity,56)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"save.json"
            s.save(path)
            restored,_=GameState.load(path)
            self.assertEqual(restored.plot_level,MAX_PLOT_LEVEL)
            self.assertEqual(restored.capacity,56)

    def test_legacy_over_capacity_collection_and_cargo_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"save.json"
            s=GameState()
            s.save(path,now=1000)
            data=json.loads(path.read_text())
            data.update(version=2)
            data.pop("plot_level")
            data.pop("base_slots")
            data["owned"][0]=25
            data["levels"][0]=[2]*25
            data["cargo"]=1
            path.write_text(json.dumps(data))
            loaded,_=GameState.load(path,now=1000)
            self.assertEqual(loaded.capacity,32)
            self.assertEqual(loaded.owned[0],25)
            self.assertEqual(loaded.cargo,1)
            self.assertTrue(loaded.deposit())
            loaded.save(path,now=1000)
            again,_=GameState.load(path,now=1000)
            self.assertEqual(again.capacity,32)
            self.assertEqual(again.used_slots,26)

    def test_invalid_capacity_saves_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"save.json"
            GameState().save(path)
            data=json.loads(path.read_text())
            for key,value in (("plot_level",7),("plot_level",True),("base_slots",7),("base_slots",9)):
                broken=dict(data)
                broken[key]=value
                path.write_text(json.dumps(broken))
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    GameState.load(path)


class PlotInterfaceTests(unittest.TestCase):
    def test_sell_cancel_confirm_last_unit_and_expand_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            g=Game(Path(directory)/"save.json",smoke=True)
            try:
                g.state.capture(0);g.state.deposit()
                g.world.interact(g)
                g.draw()
                with patch.object(g,"mouse",return_value=(1000,730)):
                    g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1))
                self.assertEqual(g.modal,"sell")
                g.draw()
                g.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
                self.assertEqual(g.state.owned[0],1)
                g.request_sale(0,0)
                g.draw()
                with patch.object(g,"mouse",return_value=(700,485)):
                    g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1))
                self.assertEqual(g.state.owned[0],0)
                self.assertFalse(g.modal)
                g.draw()
                self.assertIsNone(g.inventory.selected)
                original=g.world.home.copy()
                g.state.coins=1000
                cooldown=g.world.encounters[0]
                cooldown["cooldown"]=12
                g.expand_plot()
                self.assertGreater(g.world.home.width,original.width)
                self.assertGreater(g.world.home.height,original.height)
                self.assertEqual(tuple(g.world.player),SPAWN)
                self.assertEqual(g.world.encounters[0]["cooldown"],12)
                self.assertEqual(g.state.capacity,16)
                saved,_=GameState.load(g.path)
                self.assertEqual(saved.plot_level,1)
                g.view="world"
                g.draw()
            finally:
                pygame.quit()

    def test_full_plot_prevents_catch_and_keeps_wild_spawn(self):
        with tempfile.TemporaryDirectory() as directory:
            g=Game(Path(directory)/"save.json",smoke=True)
            try:
                fill(g.state)
                g.world.player.update(g.world.encounters[0]["pos"])
                for _ in range(100):
                    g.world.update(.02,(0,0),True,g)
                self.assertIsNone(g.state.cargo)
                self.assertEqual(g.world.encounters[0]["cooldown"],0)
                self.assertEqual(g.world.progress,0)
                g.world.interact(g)
                self.assertIn("plný",g.notice)
                g.draw()
            finally:
                pygame.quit()

    def test_plot_fences_and_north_entrance_for_every_size(self):
        pygame.init()
        try:
            for level in range(MAX_PLOT_LEVEL+1):
                w=World(level)
                s=GameState(plot_level=level)
                self.assertTrue(w.blocked(pygame.Vector2(w.home.left,w.home.centery),s))
                self.assertFalse(w.blocked(pygame.Vector2(640,w.home.top),s))
                self.assertTrue(w.at_home)
        finally:
            pygame.quit()
