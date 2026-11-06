"""Game rules and versioned saves; independent of the rendering library."""
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import time


@dataclass(frozen=True)
class Brainrot:
    name: str
    rarity: str
    cost: int
    production: int
    location: int
    color: str
    shape: str


BRAINROTS = (
    Brainrot("Tung Tung Tung Sahur", "COMMON", 25, 1, 0, "#d7ad80", "log"),
    Brainrot("Tralalero Tralala", "RARE", 180, 7, 0, "#75c5f0", "shark"),
    Brainrot("Brr Brr Patapim", "EPIC", 1200, 38, 1, "#98cb80", "tree"),
    Brainrot("Ballerina Cappuccina", "EPIC", 6500, 170, 1, "#f4a9cf", "cup"),
    Brainrot("Bombardiro Crocodilo", "LEGENDARY", 32000, 760, 2, "#e4c165", "croc"),
    Brainrot("La Vacca Saturno", "MYTHICAL", 175000, 3400, 2, "#c0a2f1", "planet"),
    Brainrot("Chimpanzini Bananini", "MYTHICAL", 320000, 8500, 3, "#edd067", "banana"),
    Brainrot("Bananita Dolphinita", "MYTHICAL", 560000, 14000, 3, "#77dccc", "dolphin"),
    Brainrot("Frigo Camelo", "CELESTIAL", 1100000, 29000, 4, "#acdff2", "fridge"),
    Brainrot("Penguino Cocosino", "CELESTIAL", 1800000, 45000, 4, "#d3edf7", "penguin"),
    Brainrot("Dragon Cannelloni", "DIVINE", 3600000, 95000, 5, "#f79869", "dragon"),
    Brainrot("Cactus Hipopotamo", "DIVINE", 6500000, 160000, 5, "#a4d87c", "cactus"),
    Brainrot("Neon Capybara", "SECRET", 13000000, 340000, 6, "#f29fe2", "capybara"),
    Brainrot("Disco Axolotlo", "SECRET", 21000000, 520000, 6, "#a89df3", "axolotl"),
    Brainrot("Il Re del Brainrot", "TRANSCENDENT", 45000000, 1100000, 7, "#f6d379", "king"),
    Brainrot("Serafino Galattico", "TRANSCENDENT", 80000000, 1900000, 7, "#e6ddff", "angel"),
)
LOCATIONS = (("Meme louka", 0), ("Brainrot city", 3500), ("Kosmické impérium", 65000),
             ("Banánová džungle", 650000), ("Ledové království", 3500000),
             ("Lávové údolí", 18000000), ("Neonová dimenze", 95000000),
             ("Nebeský chrám", 500000000))
ACHIEVEMENTS = (
    ("První zaměstnanec", "Získej svého prvního Brainrota."),
    ("Malá armáda", "Vlastni celkem 10 Brainrotů."),
    ("První milion", "Vydělej celkem 1 000 000 Coins."),
    ("Za hranice dvorku", "Odemkni druhou lokaci."),
    ("Nový začátek", "Proveď první prestige."),
    ("Celá parta", "Vlastni každý druh Brainrota."),
)
OFFLINE_LIMIT = 8 * 60 * 60
PRESTIGE_COST = 1_000_000
MAX_VALUE = 1e100
BASE_SLOTS = 8
SLOTS_PER_EXPANSION = 8
MAX_PLOT_LEVEL = 6


def save_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "BrainrotBorough" / "save.json"


@dataclass
class GameState:
    coins: float = 100.0
    earned: float = 0.0
    run_earned: float = 0.0
    owned: list = field(default_factory=lambda: [0] * len(BRAINROTS))
    levels: list = field(default_factory=lambda: [[] for _ in BRAINROTS])
    location: int = 0
    prestige: int = 0
    achievements: list = field(default_factory=list)
    cargo: int | None = None
    plot_level: int = 0
    base_slots: int = BASE_SLOTS

    @property
    def capacity(self):
        return self.base_slots + self.plot_level*SLOTS_PER_EXPANSION

    @property
    def used_slots(self):
        return sum(self.owned) + (self.cargo is not None)

    @property
    def expansion_price(self):
        return 1000 * 4**self.plot_level

    def expand_plot(self):
        if self.plot_level >= MAX_PLOT_LEVEL or self.coins < self.expansion_price:
            return False
        self.coins -= self.expansion_price
        self.plot_level += 1
        return True

    def sell_price(self, index, unit):
        if not 0 <= index < len(BRAINROTS) or not 0 <= unit < len(self.levels[index]):
            return 0
        return math.ceil(BRAINROTS[index].cost*self.levels[index][unit]*.5)

    def sell(self, index, unit):
        price = self.sell_price(index,unit)
        if not price:
            return False
        del self.levels[index][unit]
        self.owned[index] -= 1
        # Selling frees a slot; it is not production income for prestige.
        self.coins = min(MAX_VALUE,self.coins+price)
        return True

    def capture(self, index):
        if self.cargo is not None or BRAINROTS[index].location > self.location or self.used_slots >= self.capacity:
            return False
        self.cargo = index
        return True

    def deposit(self):
        if self.cargo is None:
            return False
        self.owned[self.cargo] += 1
        self.levels[self.cargo].append(1)
        self.cargo = None
        self.check_achievements()
        return True

    @property
    def multiplier(self):
        return 1 + self.prestige * 0.25

    def production(self, index):
        return BRAINROTS[index].production * sum(self.levels[index]) * self.multiplier

    @property
    def income(self):
        return sum(self.production(i) for i in range(len(BRAINROTS)))

    def upgrade_price(self, index, unit=0):
        level = self.levels[index][unit] if 0 <= unit < len(self.levels[index]) else 1
        return math.ceil(BRAINROTS[index].cost * 3 * 2.1 ** (level - 1))

    def gain(self, amount):
        amount = max(0, min(amount, MAX_VALUE))
        self.coins = min(MAX_VALUE, self.coins + amount)
        self.earned = min(MAX_VALUE, self.earned + amount)
        self.run_earned = min(MAX_VALUE, self.run_earned + amount)
        self.check_achievements()

    def tick(self, seconds):
        amount = self.income * max(0, seconds)
        self.gain(amount)
        return amount

    def upgrade(self, index, unit=0):
        price = self.upgrade_price(index, unit)
        if not 0 <= unit < len(self.levels[index]) or self.coins < price or self.levels[index][unit] >= 100:
            return False
        self.coins -= price
        self.levels[index][unit] += 1
        return True

    def unlock(self):
        if self.location >= len(LOCATIONS) - 1:
            return False
        cost = LOCATIONS[self.location + 1][1]
        if self.coins < cost:
            return False
        self.coins -= cost
        self.location += 1
        self.check_achievements()
        return True

    @property
    def prestige_reward(self):
        return math.isqrt(int(self.run_earned / PRESTIGE_COST))

    def ascend(self):
        reward = self.prestige_reward
        if not reward:
            return False
        self.prestige += reward
        self.coins = 100
        self.run_earned = 0
        self.owned = [0] * len(BRAINROTS)
        self.levels = [[] for _ in BRAINROTS]
        self.location = 0
        self.cargo = None
        self.check_achievements()
        return True

    def check_achievements(self):
        conditions = (sum(self.owned) >= 1, sum(self.owned) >= 10, self.earned >= 1e6,
                      self.location >= 1, self.prestige >= 1, all(self.owned))
        for index, condition in enumerate(conditions):
            if condition and index not in self.achievements:
                self.achievements.append(index)

    def save(self, path=None, now=None):
        path = Path(path) if path is not None else save_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(vars(self), version=3, saved_at=time.time() if now is None else now)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def load(cls, path=None, now=None):
        path = Path(path) if path is not None else save_path()
        if not path.exists():
            return cls(), 0.0
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] not in (1, 2, 3):
            raise ValueError("Neznámý formát uložené hry.")
        def number(key, maximum=MAX_VALUE, integer=False):
            value = data[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= maximum:
                raise ValueError("Neplatná hodnota: " + key)
            if integer and type(value) is not int:
                raise ValueError("Neplatné celé číslo: " + key)
            return value
        coins, earned, run = (number(k) for k in ("coins", "earned", "run_earned"))
        location, prestige = number("location", len(LOCATIONS)-1, True), number("prestige", 10**50, True)
        owned, levels = data["owned"], data["levels"]
        count = len(owned) if isinstance(owned, list) else 0
        if count not in ((6, len(BRAINROTS)) if data["version"] == 1 else (len(BRAINROTS),)) or any(
                type(v) is not int or v < 0 for v in owned):
            raise ValueError("Neplatná kolekce: owned")
        if not isinstance(levels, list) or len(levels) != count:
            raise ValueError("Neplatná kolekce: levels")
        if data["version"] == 1:
            if any(type(v) is not int or not 1 <= v <= 100 for v in levels):
                raise ValueError("Neplatné starší levely.")
            levels = [[level]*amount for level, amount in zip(levels, owned)]
        if any(not isinstance(units, list) or len(units) != amount or any(
                type(v) is not int or not 1 <= v <= 100 for v in units) for units, amount in zip(levels, owned)):
            raise ValueError("Neplatné levely jednotlivých Brainrotů.")
        owned = owned + [0]*(len(BRAINROTS)-count)
        levels = levels + [[] for _ in range(len(BRAINROTS)-count)]
        achievements = data["achievements"]
        if not isinstance(achievements, list) or any(type(v) is not int or not 0 <= v < len(ACHIEVEMENTS) for v in achievements):
            raise ValueError("Neplatné achievementy.")
        saved_at = number("saved_at", 1e12)
        state = cls(coins, earned, run, owned, levels, location, prestige, list(set(achievements)))
        cargo = data.get("cargo")
        if cargo is not None and (type(cargo) is not int or not 0 <= cargo < len(BRAINROTS)
                                  or BRAINROTS[cargo].location > location):
            raise ValueError("Neplatný nesený Brainrot.")
        state.cargo = cargo
        if data["version"] < 3:
            state.base_slots = max(BASE_SLOTS,math.ceil(state.used_slots/SLOTS_PER_EXPANSION)*SLOTS_PER_EXPANSION)
        else:
            state.plot_level = number("plot_level",MAX_PLOT_LEVEL,True)
            state.base_slots = number("base_slots",MAX_VALUE,True)
            if state.base_slots < BASE_SLOTS or state.base_slots % SLOTS_PER_EXPANSION or state.used_slots > state.capacity:
                raise ValueError("Neplatná kapacita pozemku.")
        elapsed = min(OFFLINE_LIMIT, max(0, (time.time() if now is None else now) - saved_at))
        offline = state.tick(elapsed)
        return state, offline
