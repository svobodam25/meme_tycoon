"""A virtualized grid of individual Brainrots and plot management."""
import math

import pygame

from game_state import BRAINROTS, LOCATIONS, MAX_PLOT_LEVEL, SLOTS_PER_EXPANSION

GRID = pygame.Rect(28, 234, 824, 504)
COLS, STEP_X, STEP_Y = 5, 164, 168
CARD_W, CARD_H = 152, 156


class Inventory:
    def __init__(self):
        self.scroll = 0
        self.selected = None

    @staticmethod
    def item(state, slot):
        """Resolve a flat slot without allocating a list of the whole collection."""
        if slot < 0:
            return None
        for species, amount in enumerate(state.owned):
            if slot < amount:
                return species, slot
            slot -= amount
        return None

    @staticmethod
    def index(state, item):
        if item is None:
            return 0
        species, unit = item
        return sum(state.owned[:species]) + unit

    @staticmethod
    def max_scroll(state):
        return max(0, math.ceil(sum(state.owned)/COLS)*STEP_Y-GRID.height)

    def clamp(self, state):
        self.scroll = max(0, min(self.max_scroll(state), self.scroll))
        if self.selected is not None:
            species, unit = self.selected
            if unit >= state.owned[species]:
                self.selected = None
        if self.selected is None:
            self.selected = self.item(state, 0)

    def handle_event(self, game, event):
        self.clamp(game.state)
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y*64
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):
                self.scroll += GRID.height*(-1 if event.key == pygame.K_PAGEUP else 1)
            elif event.key in (pygame.K_HOME,pygame.K_END):
                self.scroll = 0 if event.key == pygame.K_HOME else self.max_scroll(game.state)
            elif event.key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN):
                delta = {pygame.K_LEFT:-1,pygame.K_RIGHT:1,pygame.K_UP:-COLS,pygame.K_DOWN:COLS}[event.key]
                slot = max(0,min(sum(game.state.owned)-1,self.index(game.state,self.selected)+delta))
                self.selected = self.item(game.state,slot)
                row_y = slot//COLS*STEP_Y
                if row_y < self.scroll:
                    self.scroll = row_y
                elif row_y+CARD_H > self.scroll+GRID.height:
                    self.scroll = row_y+CARD_H-GRID.height
        self.clamp(game.state)

    @staticmethod
    def name(game, name, x, y, width, size=14):
        """Wrap at word boundaries so full names remain legible in small slots."""
        words, lines, current = name.split(), [], ""
        key = (size,True)
        if key not in game.fonts:
            game.fonts[key] = pygame.font.SysFont("segoeui,dejavusans,arial",size,True)
        font = game.fonts[key]
        for word in words:
            candidate = (current+" "+word).strip()
            if current and font.size(candidate)[0] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        for row,line in enumerate(lines):
            game.text(line,x,y+row*(size+3),size,"#eef1e7",True)

    def draw(self, game):
        state = game.state
        self.clamp(state)
        total = sum(state.owned)
        game.text("TVŮJ INVENTÁŘ",28,175,28,"#eef1e7",True)
        full = state.used_slots >= state.capacity
        game.text(f"{state.used_slots} / {state.capacity} slotů · Pozemek Lv {state.plot_level+1}"+(" · PLNO" if full else ""),28,211,16,"#efb2a0" if full else "#98a5b7")
        expansion = f"Pozemek +{SLOTS_PER_EXPANSION} slotů · {self.short(state.expansion_price)} Coins" if state.plot_level < MAX_PLOT_LEVEL else "Pozemek plně rozšířený"
        game.button(expansion,(470,179,382,43),game.expand_plot,state.plot_level<MAX_PLOT_LEVEL and state.coins>=state.expansion_price,True)
        game.box((876,177,376,571),"#1b2330",18)
        if not total:
            game.box(GRID,"#19212d",18)
            game.text("Tvoje sbírka začíná prvním úlovkem.",72,411,25,"#eef1e7",True)
            game.text("Vydej se na sever, podrž E u Brainrota a dones ho domů.",72,457,17,"#98a5b7")
            game.text(f"Místo pro {state.capacity} Brainrotů.",902,213,22,"#d3f878",True)
            game.text("Více místa? Rozšiř svůj pozemek.",902,254,17,"#98a5b7")
            game.character(1060,416,"log",BRAINROTS[0].color,1.6)
            game.button("Vyrazit na lov",(902,662,324,52),game.close_menu,True,True)
            return
        old_clip = game.surface.get_clip()
        game.surface.set_clip(GRID)
        first = int(self.scroll//STEP_Y)*COLS
        last = min(total,(int((self.scroll+GRID.height)//STEP_Y)+1)*COLS)
        for slot in range(first,last):
            species, unit = self.item(state,slot)
            b = BRAINROTS[species]
            level = state.levels[species][unit]
            x = GRID.x+(slot%COLS)*STEP_X
            y = GRID.y+(slot//COLS)*STEP_Y-self.scroll
            rect = pygame.Rect(x,y,CARD_W,CARD_H)
            selected = self.selected == (species,unit)
            hover = rect.collidepoint(game.mouse()) and GRID.collidepoint(game.mouse()) and not game.modal
            game.box(rect,"#2a3848" if selected or hover else "#1b2532",14)
            game.box(rect,b.color if selected else "#354052",14,2 if selected else 1)
            game.box((x+12,y+12,5,23),b.color,2)
            game.character(x+76,y+77,b.shape,b.color,.64)
            game.box((x+20,y+9,57,21),"#1b2532",5)
            game.box((x+95,y+9,50,21),"#1b2532",5)
            game.text(f"#{unit+1}",x+24,y+12,13,"#b6c1cc",True)
            game.text(f"Lv {level}",x+101,y+12,13,"#d3f878",True)
            self.name(game,b.name,x+12,y+118,128)
            hitbox = rect.clip(GRID)
            game.buttons.append((hitbox,lambda item=(species,unit):setattr(self,"selected",item)))
        game.surface.set_clip(old_clip)
        maximum = self.max_scroll(state)
        if maximum:
            game.box((856,GRID.y,5,GRID.height),"#2d3949",2)
            thumb_h = max(24,GRID.height**2/(maximum+GRID.height))
            thumb_y = GRID.y+(GRID.height-thumb_h)*self.scroll/maximum
            game.box((856,thumb_y,5,thumb_h),"#b6cf92",2)
        species,unit = self.selected
        b = BRAINROTS[species]
        level = state.levels[species][unit]
        game.text(b.rarity,902,201,13,b.color,True)
        self.name(game,b.name,902,232,326,22)
        game.character(1064,415,b.shape,b.color,1.55)
        game.text(f"Kus #{unit+1} · Level {level}",902,528,23,"#eef1e7",True)
        game.text(f"Produkce {self.short(b.production*level*state.multiplier)} Coins / s",902,568,18,"#d3f878")
        game.text(f"Původ: {LOCATIONS[b.location][0]}",902,601,15,"#98a5b7")
        price = state.upgrade_price(species,unit)
        label = f"Vylepšit · {self.short(price)} Coins" if level < 100 else "Maximální level 100"
        game.button(label,(902,662,324,52),lambda:game.upgrade(species,unit),level<100 and state.coins>=price,True)
        game.button(f"Prodat · {self.short(state.sell_price(species,unit))} Coins",(902,719,324,28),lambda:game.request_sale(species,unit))
        game.text("Kolečko: posouvat · Šipky: vybrat · Home / End: začátek / konec",28,752,15,"#98a5b7")

    @staticmethod
    def short(value):
        for divisor,suffix in ((1e12,"T"),(1e9,"B"),(1e6,"M"),(1e3,"k")):
            if value >= divisor:
                return f"{value/divisor:.2f}".rstrip("0").rstrip(".")+suffix
        return f"{value:.0f}"
