import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from game_state import BRAINROTS, LOCATIONS, GameState, OFFLINE_LIMIT, save_path


def catch(state, index):
    assert state.capture(index)
    assert state.deposit()


class EconomyTests(unittest.TestCase):
    def test_upgrade_diminishing_returns_prices_and_rarity_hierarchy(self):
        for index, brainrot in enumerate(BRAINROTS):
            s = GameState(coins=1e15, location=7)
            catch(s, index)
            first_price = s.upgrade_price(index)
            self.assertGreaterEqual(first_price / s.upgrade_gain(index), 590)
            before = s.income
            self.assertTrue(s.upgrade(index))
            self.assertGreater(s.income-before, 0)
            self.assertLess(s.income-before, brainrot.production)
            self.assertEqual(s.used_slots, 1)
            self.assertLess(s.sell_price(index, 0), brainrot.cost/2+first_price)
            previous_gain = float('inf')
            previous_price = 0
            for level in range(1, 100):
                s.levels[index][0] = level
                gain = s.upgrade_gain(index)
                price = s.upgrade_price(index)
                sale_before = s.sell_price(index, 0)
                s.levels[index][0] += 1
                sale_after = s.sell_price(index, 0)
                s.levels[index][0] -= 1
                self.assertGreater(gain, 0)
                self.assertLess(gain, previous_gain)
                self.assertGreaterEqual(price, previous_price)
                self.assertGreaterEqual(price/gain, 590)
                self.assertLess(sale_after-sale_before, price)
                previous_gain, previous_price = gain, price
            next_rarity = next((b for b in BRAINROTS[index+1:] if b.rarity != brainrot.rarity), None)
            if next_rarity:
                self.assertLess(s.unit_production(index, 100), next_rarity.production)
            self.assertLessEqual(s.unit_production(index, 100), brainrot.production*3)
            s.levels[index][0] = 99
            price = s.upgrade_price(index)
            s.coins = price-1
            self.assertFalse(s.upgrade(index))
            s.coins = price
            self.assertTrue(s.upgrade(index))
            self.assertEqual(s.coins, 0)
            self.assertEqual(s.levels[index][0], 100)
            self.assertFalse(s.upgrade(index))

    def test_renamed_save_migrates_without_overwriting_old_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', LOCALAPPDATA=directory):
            legacy = Path(directory)/'BrainrotBorough'/'save.json'
            s = GameState(coins=1234)
            catch(s, 0)
            s.levels[0][0] = 10
            s.save(legacy, now=1000)
            original = legacy.read_bytes()
            loaded, _ = GameState.load(now=1000)
            self.assertEqual(loaded.coins, 1234)
            self.assertEqual(loaded.levels[0], [10])
            self.assertEqual(save_path(), Path(directory)/'MemeTycoon'/'save.json')
            loaded.coins = 5678
            loaded.save(now=1000)
            self.assertEqual(legacy.read_bytes(), original)
            loaded, _ = GameState.load(now=1000)
            self.assertEqual(loaded.coins, 5678)
            fresh, _ = GameState.load(Path(directory)/'custom.json', now=1000)
            self.assertEqual(fresh.coins, 100)

    def test_new_achievements_unlock_and_survive_prestige(self):
        s = GameState(coins=1e12, location=7)
        self.assertTrue(s.expand_plot())
        self.assertIn(6, s.achievements)
        catch(s, 4)
        self.assertIn(10, s.achievements)
        catch(s, 12)
        catch(s, 13)
        self.assertIn(11, s.achievements)
        s.levels[4][0] = 9
        self.assertTrue(s.upgrade(4))
        self.assertIn(8, s.achievements)
        s.run_earned = s.prestige_price
        before = set(s.achievements)
        s.ascend()
        self.assertTrue(before <= set(s.achievements))

    def test_leaderboards_rank_save_and_validate_completed_eras(self):
        s = GameState()
        for era in range(1, 9):
            catch(s, 0)
            s.levels[0][0] = era
            s.run_earned = s.prestige_price
            self.assertTrue(s.ascend())
        self.assertLessEqual(len(s.records), 15)
        self.assertEqual(s.leaderboard('income')[0]['era'], 8)
        self.assertEqual(s.leaderboard('collection')[0]['era'], 1)
        self.assertEqual(len(s.leaderboard('earned')), 5)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'save.json'
            s.save(path, now=1000)
            loaded, _ = GameState.load(path, now=1000)
            self.assertEqual(loaded.records, s.records)
            data = json.loads(path.read_text())
            data['records'][0]['income'] = -1
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                GameState.load(path, now=1000)

    def test_shop_discovery_cost_capacity_and_level(self):
        s = GameState(coins=10_000)
        self.assertFalse(s.buy(0))
        self.assertFalse(s.buy(-1))
        self.assertFalse(s.buy(len(BRAINROTS)))
        self.assertTrue(s.capture(0))
        self.assertFalse(s.buy(0))
        s.deposit()
        s.sell(0, 0)
        price = s.purchase_price(0)
        self.assertEqual(price, 100)
        s.coins = price - 1
        self.assertFalse(s.buy(0))
        s.coins = price
        self.assertTrue(s.buy(0))
        self.assertEqual((s.coins, s.levels[0]), (0, [1]))
        s.coins = 100_000
        for _ in range(s.capacity - 2):
            catch(s, 0)
        s.capture(1)
        self.assertFalse(s.buy(0))

    def test_prestige_doubles_income_and_quadruples_requirement(self):
        s = GameState()
        for level in range(5):
            self.assertEqual(s.prestige_price, 1_000_000 * 4**level)
            self.assertEqual(s.multiplier, 2**level)
            s.run_earned = s.prestige_price - 1
            self.assertFalse(s.ascend())
            s.run_earned += 1
            self.assertTrue(s.ascend())
            self.assertEqual(s.prestige, level + 1)

    def test_discovery_survives_save_sale_and_prestige(self):
        s = GameState(location=1)
        catch(s, 2)
        s.sell(2, 0)
        s.run_earned = s.prestige_price
        s.ascend()
        self.assertIn(2, s.discovered)
        s.coins = 100_000
        self.assertFalse(s.buy(2))
        s.unlock()
        self.assertTrue(s.buy(2))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"save.json"
            s.save(path, now=1000)
            loaded, _ = GameState.load(path, now=1000)
            self.assertEqual(loaded.discovered, [2])
            data = json.loads(path.read_text())
            data.update(version=3)
            del data['discovered']
            path.write_text(json.dumps(data))
            loaded, _ = GameState.load(path, now=1000)
            self.assertEqual(loaded.discovered, [2])

    def test_capture_income_and_individual_upgrade(self):
        s = GameState()
        catch(s, 0)
        catch(s, 0)
        self.assertEqual(s.coins, 100)
        self.assertEqual(s.income, 2)
        self.assertEqual(s.tick(10), 20)
        s.gain(100)
        self.assertTrue(s.upgrade(0, 1))
        self.assertEqual(s.levels[0], [1, 2])
        self.assertAlmostEqual(s.income, 2.301029995664)
        self.assertEqual(s.coins, 40)
        s.coins = s.upgrade_price(0, 1) - 1
        self.assertFalse(s.upgrade(0, 1))
        self.assertFalse(s.upgrade(0, 2))
        catch(s,0)
        self.assertEqual(s.levels[0], [1,2,1])
        self.assertTrue(hasattr(s,"buy"))
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
        self.assertEqual(s.prestige_reward, 1)
        self.assertTrue(s.ascend())
        self.assertEqual((s.coins, s.run_earned, s.location), (100, 0, 0))
        self.assertEqual(sum(s.owned), 0)
        self.assertEqual(s.earned, 4_000_000)
        self.assertIn(4, s.achievements)
        catch(s, 0)
        self.assertEqual(s.income, 2)

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
                               ("location", 9), ("achievements", [False]), ("version", 6)):
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

    def test_legacy_migration_preserves_individual_levels_with_new_balance(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"save.json"
            GameState().save(path,now=1000)
            data=json.loads(path.read_text())
            data.update(version=1,owned=[2,1,0,0,0,0],levels=[3,2,1,1,1,1])
            path.write_text(json.dumps(data))
            state,_=GameState.load(path,now=1000)
            self.assertEqual(state.levels[:2],[[3,3],[2]])
            self.assertAlmostEqual(state.income,12.061452479087194)
            self.assertEqual(len(state.owned),16)
            state.coins=1e6
            state.upgrade(0,1)
            state.save(path,now=1000)
            loaded,_=GameState.load(path,now=1000)
            self.assertEqual(loaded.levels[0],[3,4])


if __name__ == "__main__":
    unittest.main()
