import json
from pathlib import Path
import tempfile
import unittest

from game_state import BRAINROTS, LOCATIONS, GameState, OFFLINE_LIMIT


def catch(state, index):
    assert state.capture(index)
    assert state.deposit()


class EconomyTests(unittest.TestCase):
    def test_capture_income_and_individual_upgrade(self):
        s = GameState()
        catch(s, 0)
        catch(s, 0)
        self.assertEqual(s.coins, 100)
        self.assertEqual(s.income, 2)
        self.assertEqual(s.tick(10), 20)
        self.assertTrue(s.upgrade(0, 1))
        self.assertEqual(s.levels[0], [1, 2])
        self.assertEqual(s.income, 3)
        self.assertEqual(s.coins, 45)
        self.assertFalse(s.upgrade(0, 1))
        self.assertFalse(s.upgrade(0, 2))
        catch(s,0)
        self.assertEqual(s.levels[0], [1,2,1])
        self.assertFalse(hasattr(s,"buy"))
        self.assertIn(0, s.achievements)

    def test_locked_character_and_location_cost(self):
        s = GameState(coins=100_000)
        self.assertFalse(s.capture(2))
        self.assertTrue(s.unlock())
        self.assertEqual(s.coins, 96_500)
        catch(s, 2)
        self.assertTrue(s.unlock())
        self.assertFalse(s.unlock())

    def test_prestige_resets_run_and_keeps_lifetime(self):
        s = GameState()
        self.assertFalse(s.ascend())
        s.gain(4_000_000)
        catch(s, 0)
        s.unlock()
        self.assertEqual(s.prestige_reward, 2)
        self.assertTrue(s.ascend())
        self.assertEqual((s.coins, s.run_earned, s.location), (100, 0, 0))
        self.assertEqual(sum(s.owned), 0)
        self.assertEqual(s.earned, 4_000_000)
        self.assertIn(4, s.achievements)
        catch(s, 0)
        self.assertEqual(s.income, 1.5)

    def test_save_round_trip_and_capped_offline_income(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            s = GameState()
            catch(s, 0)
            s.save(path, now=1000)
            loaded, offline = GameState.load(path, now=1000+OFFLINE_LIMIT*2)
            self.assertEqual(offline, OFFLINE_LIMIT)
            self.assertEqual(loaded.coins, 100+OFFLINE_LIMIT)
            self.assertEqual(loaded.owned, s.owned)
            self.assertFalse(path.with_suffix(".tmp").exists())
            _, negative = GameState.load(path, now=0)
            self.assertEqual(negative, 0)

    def test_corrupted_saves_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            GameState().save(path)
            data = json.loads(path.read_text())
            for key, value in (("coins", float("nan")), ("owned", [-1]*6), ("levels", [1]),
                               ("location", 9), ("achievements", [False]), ("version", 4)):
                broken = dict(data)
                broken[key] = value
                path.write_text(json.dumps(broken))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    GameState.load(path)

    def test_new_save_capacity_and_max_level(self):
        with tempfile.TemporaryDirectory() as directory:
            s, offline = GameState.load(Path(directory)/"missing.json")
            self.assertEqual((s.coins, offline), (100, 0))
        s.coins = 1e100
        s.owned[0] = 8
        s.levels[0] = [100]*8
        self.assertFalse(s.capture(0))
        self.assertTrue(s.expand_plot())
        catch(s,0)
        self.assertEqual(s.owned[0],9)
        self.assertEqual(s.levels[0][-1],1)
        self.assertFalse(s.upgrade(0))
        before = s.coins
        s.tick(-10)
        self.assertEqual(before, s.coins)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"large.json"
            s.save(path)
            loaded,_=GameState.load(path)
            self.assertEqual(loaded.owned[0],9)

    def test_all_eight_locations_and_sixteen_species(self):
        self.assertEqual(len(LOCATIONS), 8)
        self.assertEqual(len(BRAINROTS), 16)
        s = GameState(coins=1e15)
        for level in range(8):
            self.assertEqual(s.location, level)
            for index in (level*2,level*2+1):
                if s.used_slots >= s.capacity:
                    self.assertTrue(s.expand_plot())
                catch(s,index)
                self.assertTrue(s.upgrade(index,0))
            self.assertEqual(s.unlock(),level<7)
        self.assertIn(5,s.achievements)

    def test_legacy_migration_preserves_income_and_individual_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"save.json"
            GameState().save(path,now=1000)
            data=json.loads(path.read_text())
            data.update(version=1,owned=[2,1,0,0,0,0],levels=[3,2,1,1,1,1])
            path.write_text(json.dumps(data))
            state,_=GameState.load(path,now=1000)
            self.assertEqual(state.levels[:2],[[3,3],[2]])
            self.assertEqual(state.income,20)
            self.assertEqual(len(state.owned),16)
            state.coins=1e6
            state.upgrade(0,1)
            state.save(path,now=1000)
            loaded,_=GameState.load(path,now=1000)
            self.assertEqual(loaded.levels[0],[3,4])


if __name__ == "__main__":
    unittest.main()
