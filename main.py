"""Brainrot Borough — a small, self-contained Pygame idle tycoon."""
import argparse
import math
import os
from pathlib import Path
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from game_state import ACHIEVEMENTS, BRAINROTS, LOCATIONS, PRESTIGE_COST, GameState, save_path
from world import World, THEMES

W, H = 1280, 820
BG = "#10151e"
PANEL = "#1b2330"
INK = "#f0f3eb"
MUTED = "#98a5b7"
LIME = "#d3f878"


def compact(value):
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k")):
        if value >= divisor:
            return f"{value / divisor:.2f}".rstrip("0").rstrip(".") + suffix
    return f"{value:,.0f}".replace(",", " ")


class Game:
    def __init__(self, path=None, smoke=False):
        pygame.init()
        pygame.display.set_caption("Brainrot Borough | Meme impérium")
        self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.surface = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.fonts = {}
        self.path = Path(path) if path else save_path()
        self.smoke = smoke
        self.notice = "Vítej doma! Vydej se na sever, chyť Brainrota a dones ho na pozemek."
        self.notice_until = time.monotonic() + 8
        self.save_enabled = True
        try:
            self.state, offline = GameState.load(self.path)
            if offline:
                self.notice = f"Vítej zpět! Tvá parta mezitím vydělala {compact(offline)} Coins (max. 8 h)."
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            self.state = GameState()
            # Never silently overwrite an unreadable save.
            self.save_enabled = False
            self.notice = "Uloženou hru nelze načíst. Hraješ bez ukládání; původní soubor zůstává zachován."
        self.tab = "Vylepšení"
        self.selected_units = [0]*len(BRAINROTS)
        self.sprite_cache = {}
        self.location = self.state.location
        self.buttons = []
        self.modal = False
        self.last_save = time.monotonic()
        self.sparks = []
        self.elapsed = 0
        self.view = "world"
        self.world = World()

    def text(self, text, x, y, size=18, color=INK, bold=False, center=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui,dejavusans,arial", size, bold)
        img = self.fonts[key].render(str(text), True, color)
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        self.surface.blit(img, rect)

    def box(self, rect, color=PANEL, radius=18, width=0):
        pygame.draw.rect(self.surface, color, rect, width, border_radius=radius)

    def button(self, text, rect, action, enabled=True, accent=False):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.mouse()) and not self.modal
        color = ("#e2ff9c" if hover else LIME) if accent and enabled else ("#344458" if hover and enabled else "#293547")
        self.box(rect, color, 10)
        self.text(text, rect.centerx, rect.centery, 16, "#17231c" if accent and enabled else (INK if enabled else "#6c7b90"), True, True)
        if enabled:
            self.buttons.append((rect, action))

    def mouse(self):
        x, y = pygame.mouse.get_pos()
        scale, ox, oy = self.viewport()
        return ((x - ox) / scale, (y - oy) / scale)

    def viewport(self):
        ww, wh = self.window.get_size()
        scale = min(ww / W, wh / H)
        return scale, (ww - W * scale) / 2, (wh - H * scale) / 2

    def notify(self, message):
        self.notice = message
        self.notice_until = time.monotonic() + 5

    def save(self):
        if not self.save_enabled:
            return False
        try:
            self.state.save(self.path)
            return True
        except OSError:
            self.notify("Uložení se nezdařilo. Zkontroluj volné místo a oprávnění ke složce.")
            return False

    def upgrade(self, index, unit):
        if self.state.upgrade(index, unit):
            self.notify(f"{BRAINROTS[index].name} #{unit+1}: level {self.state.levels[index][unit]}.")

    def unlock(self):
        if self.state.unlock():
            self.location = self.state.location
            self.notify(f"Nová lokace: {LOCATIONS[self.location][0]}!")

    def tap(self):
        value = max(1, self.state.income * .05)
        self.state.gain(value)
        self.sparks.append([320, 455, "+" + compact(value), 1.0])

    def character(self, x, y, kind, color, size=1, bounce=0):
        # Supersampled, cached sprites give smooth outlines at all display sizes.
        key = (kind,color,round(size,3))
        if key not in self.sprite_cache:
            target = self.surface
            self.surface = pygame.Surface((320,320),pygame.SRCALPHA)
            try:
                self._character_raw(160,160,kind,color,2)
                side = max(1,int(160*size))
                self.sprite_cache[key] = pygame.transform.smoothscale(self.surface,(side,side))
            finally:
                self.surface = target
        sprite = self.sprite_cache[key]
        self.surface.blit(sprite,sprite.get_rect(center=(round(x),round(y+bounce))))

    def _character_raw(self, x, y, kind, color, size=1, bounce=0):
        """Original vector cartoons, drawn entirely with Pygame primitives."""
        y += bounce
        def ellipse(c, r, width=0):
            pygame.draw.ellipse(self.surface, c, (x+r[0]*size, y+r[1]*size, r[2]*size, r[3]*size), width)
        def line(c, a, b, width=3):
            pygame.draw.line(self.surface, c, (x+a[0]*size, y+a[1]*size), (x+b[0]*size, y+b[1]*size), max(1, int(width*size)))
        def poly(c, points):
            pygame.draw.polygon(self.surface, c, [(x+a*size, y+b*size) for a,b in points])
        ellipse("#26352f", (-43, 51-bounce/size, 86, 16))
        if kind == "log":
            pygame.draw.rect(self.surface,"#74513f",(x-31*size,y-48*size,62*size,101*size),border_radius=int(20*size))
            pygame.draw.rect(self.surface, color, (x-28*size, y-45*size, 56*size, 95*size), border_radius=int(18*size))
            ellipse("#f0cfa3",(-24,-44,48,15))
            ellipse("#ad815e",(-15,-41,30,9),max(1,int(size)))
            line("#e9c599",(-23,-25),(-23,33),3)
            for a in (-17, 0, 17):
                line("#a37a56", (a,-32), (a-2,35), 2)
            line("#d7ad80", (28, 0), (49,-20), 7)
            line("#79553c", (48,-40), (52,24), 8)
        elif kind == "shark":
            ellipse("#346a91",(-43,-45,88,89))
            poly(color, [(-40,15),(-22,-30),(20,-42),(43,-5),(28,36),(-25,40)])
            poly(color, [(0,-30),(3,-65),(27,-32)])
            poly(color, [(-25,0),(-60,-10),(-35,30)])
            ellipse("#deeff4", (-24,0,52,41))
        elif kind == "tree":
            pygame.draw.rect(self.surface, "#ac845b", (x-16*size,y-10*size,32*size,65*size), border_radius=int(8*size))
            for a,b in ((-38,-40),(-15,-65),(10,-36)):
                ellipse(color, (a,b,50,65))
        elif kind == "cup":
            ellipse(color, (12,-35,43,48), max(1,int(7*size)))
            poly("#f8e9d7", [(-33,-42),(34,-42),(26,22),(-24,22)])
            ellipse("#91654b", (-30,-49,61,20))
            ellipse("#f5d5b4", (-16,-45,29,12))
            poly(color, [(-20,22),(20,22),(47,45),(-47,45)])
        elif kind == "croc":
            poly(color, [(-50,-12),(-10,-40),(44,-23),(55,8),(22,30),(-38,22)])
            poly("#a7b98a", [(-12,-22),(-22,-62),(9,-32),(20,-14),(64,36),(9,22)])
            line("#557c5f", (-43,10),(45,10),3)
            for a in (-25,-10,5,20):
                poly("#fff5d4", [(a,9),(a+7,9),(a+3,17)])
        elif kind == "planet":
            ellipse(color, (-37,-43,74,86))
            ellipse("#f8de96", (-63,-10,126,36), max(1,int(7*size)))
            ellipse("#7965aa", (-21,-27,21,25))
            poly("#fff0c2", [(-25,-35),(-39,-58),(-9,-43)])
            poly("#fff0c2", [(20,-35),(38,-57),(9,-43)])
        elif kind in ("banana","dolphin"):
            poly("#aa8737",[(-35,33),(-43,-30),(-20,-59),(-10,-21),(15,11),(43,23),(22,42)])
            poly(color,[(-31,30),(-37,-29),(-21,-48),(-15,-16),(13,15),(39,25),(20,36)])
            if kind == "banana":
                ellipse("#94643e",(-27,-34,54,64))
                ellipse("#edc696",(-21,-25,42,47))
                for a in (-33,21):
                    ellipse("#94643e",(a,-26,15,22))
            else:
                ellipse("#82d4db",(-27,-35,58,65))
                poly("#82d4db",[(-20,-20),(-51,-5),(-23,6)])
                poly("#6bb2ca",[(12,-29),(32,-58),(34,-13)])
        elif kind in ("fridge","penguin"):
            if kind == "fridge":
                pygame.draw.rect(self.surface,"#6093b0",(x-33*size,y-53*size,66*size,104*size),border_radius=int(9*size))
                pygame.draw.rect(self.surface,color,(x-29*size,y-49*size,58*size,96*size),border_radius=int(6*size))
                line("#649bbb",(-28,5),(28,5),3)
                line("#f8ffff",(21,12),(21,33),4)
                poly("#f7fbfa",[(-25,-49),(-12,-65),(1,-49)])
            else:
                ellipse("#304c6a",(-34,-49,68,99))
                ellipse(color,(-25,-20,50,65))
                poly("#f6ce76",[(-8,-2),(12,-2),(1,10)])
                poly("#304c6a",[(-25,-12),(-49,20),(-25,15)])
                poly("#304c6a",[(25,-12),(49,20),(25,15)])
        elif kind in ("dragon","cactus"):
            ellipse("#3c6655",(-35,-44,70,94))
            ellipse(color,(-30,-42,60,90))
            ellipse("#e6d298",(-21,0,42,44))
            if kind == "dragon":
                for side in (-1,1):
                    poly("#bf5e55",[(side*22,-14),(side*64,-48),(side*53,20),(side*25,23)])
                    poly(color,[(side*18,-35),(side*30,-65),(side*4,-38)])
                for y1 in (7,19,31):
                    line("#bd9d69",(-14,y1),(14,y1),2)
            else:
                for a in (-20,0,20):
                    line("#669c61",(a,-33),(a,30),2)
                    for yy in (-28,0,28):
                        line("#f2e2b2",(a,yy),(a+6,yy-5),2)
                poly(color,[(-25,7),(-49,7),(-49,-26),(-39,-26),(-39,-3),(-25,-3)])
        elif kind in ("capybara","axolotl"):
            if kind == "axolotl":
                for side in (-1,1):
                    for yy in (-31,-13,5):
                        line("#ee99d0",(side*23,yy),(side*48,yy-12),7)
            ellipse("#815c88",(-36,-44,72,93))
            ellipse(color,(-32,-41,64,87))
            ellipse("#f7cfdc",(-23,-2,46,29))
            for a in (-23,12):
                ellipse(color,(a,-51,16,24))
            if kind == "capybara":
                line("#fff3b6",(-24,-38),(25,-38),4)
                ellipse("#f5c65c",(-7,-58,20,19))
        else:
            if kind == "angel":
                for side in (-1,1):
                    for n in range(3):
                        ellipse("#fcf4dd",(side*(30+n*9)-13,-43+n*15,28,49))
                ellipse("#fce29b",(-28,-67,56,15),max(1,int(3*size)))
            ellipse("#a883b5",(-32,-40,64,92))
            ellipse(color,(-28,-36,56,82))
            poly("#dfac56",[(-29,-36),(-37,-66),(-12,-53),(0,-77),(13,-53),(35,-66),(28,-36)])
            ellipse("#ee847b",(-5,-55,10,13))
        # Big eyes and tiny sneakers give the whole collection a consistent style.
        for a in (-12,12):
            ellipse("#fffaf0", (a-8,-22,17,22))
            ellipse("#182533", (a-2,-15,7,11))
            ellipse("#ffffff", (a-1,-15,3,4))
            line("#283449", (a,40),(a,53),5)
            ellipse("#a9cbff", (a-11,49,26,12))
        if kind not in ("croc", "cup"):
            pygame.draw.arc(self.surface, "#293545", (x-10*size,y+3*size,20*size,14*size), math.pi, math.tau, max(1,int(2*size)))

    def scene(self):
        s = self.state
        self.box((28, 177, 526, 422), THEMES[self.location][0])
        self.text("TVÉ IMPÉRIUM", 52, 197, 13, "#b5c9b7", True)
        self.text(LOCATIONS[self.location][0], 52, 221, 29, INK, True)
        # Skyline and a small cartoon world.
        for i in range(7):
            height = 42 + (i*31)%66
            self.box((48+i*70, 395-height, 51, height), "#40544d" if self.location == 0 else "#47415e", 5)
            for j in range(2):
                self.box((59+i*70+j*18, 409-height, 7, 10), "#78927a", 2)
        pygame.draw.ellipse(self.surface, "#547257", (45,360,494,200))
        pygame.draw.ellipse(self.surface, "#6f9062", (65,369,454,143))
        owned = [i for i,b in enumerate(BRAINROTS) if s.owned[i] and b.location == self.location]
        if owned:
            actors = [i for i in owned for _ in range(min(s.owned[i],3))][:6]
            for n,i in enumerate(actors):
                x = 120+(n%3)*157
                y = 369+(n//3)*85
                self.character(x,y,BRAINROTS[i].shape,BRAINROTS[i].color,.72,math.sin(self.elapsed*2.5+n)*5)
        else:
            self.character(295,390,"log","#d7ad80",1.15,math.sin(self.elapsed*2)*4)
            self.text("Tady začíná tvoje meme éra.", 292, 522, 17, INK, center=True)
        self.button("+ Rozjeď hype · klikni", (155,546,270,37), self.tap, accent=True)
        self.box((28,615,526,137))
        self.text("DALŠÍ ZASTÁVKA", 50,634,13,MUTED,True)
        if s.location < len(LOCATIONS)-1:
            name, cost = LOCATIONS[s.location+1]
            self.text(name,50,659,21,INK,True)
            self.text("Noví Brainroti, větší výdělky.",50,698,15,MUTED)
            self.button(f"Odemknout · {compact(cost)}",(313,684,218,43),self.unlock,s.coins>=cost,True)
        else:
            self.text("Vesmír ti leží u nohou.",50,662,24,INK,True)
            self.text("Další výzva? Prestige a ještě silnější parta.",50,704,16,MUTED)

    def select_unit(self, index, delta):
        self.selected_units[index] = max(0,min(self.state.owned[index]-1,self.selected_units[index]+delta))

    def upgrades(self):
        s = self.state
        self.text("Tvoje parta · jednotlivá vylepšení",587,178,23,INK,True)
        self.text("Vyber konkrétního Brainrota. Další členy získáš pouze lovem.",587,212,15,MUTED)
        for row,i in enumerate(range(self.location*2,self.location*2+2)):
            b = BRAINROTS[i]
            unit = min(self.selected_units[i],max(0,s.owned[i]-1))
            level = s.levels[i][unit] if s.owned[i] else 1
            y = 252+row*240
            self.box((580,y,672,224))
            self.box((598,y+18,112,127),"#263243",14)
            self.character(654,y+79,b.shape,b.color,.77,math.sin(self.elapsed*2+row)*3)
            self.text(b.rarity,730,y+18,13,b.color,True)
            self.text(b.name,730,y+43,23,INK,True)
            self.text(f"{compact(b.production*level*s.multiplier)} / s · Level {level}" if s.owned[i] else "Zatím nechycený · vydej se na lov",730,y+82,17,LIME if s.owned[i] else MUTED)
            self.text(f"Vlastníš {s.owned[i]} · Celkem {compact(s.production(i))} / s",730,y+112,16,MUTED)
            self.button("<",(598,y+162,43,44),lambda i=i:self.select_unit(i,-1),unit>0)
            self.text(f"Kus {unit+1} / {s.owned[i]}" if s.owned[i] else "Žádný úlovek",747,y+184,17,INK,True,True)
            self.button(">",(853,y+162,43,44),lambda i=i:self.select_unit(i,1),unit+1<s.owned[i])
            label = "Maximální level 100" if level >= 100 else f"Vylepšit #{unit+1} · {compact(s.upgrade_price(i,unit))}"
            self.button(label if s.owned[i] else "Nejprve chyť na mapě",(916,y+162,318,44),lambda i=i,unit=unit:self.upgrade(i,unit),s.owned[i]>0 and s.coins>=s.upgrade_price(i,unit) and level<100,True)
        self.text("Každý kus má vlastní level. Nový úlovek začíná na levelu 1.",589,744,15,MUTED)

    def milestones(self):
        self.text("Každé impérium má svůj příběh.",587,181,24,INK,True)
        self.text(f"Splněno {len(self.state.achievements)} / {len(ACHIEVEMENTS)}",587,219,16,LIME)
        for i,(title,detail) in enumerate(ACHIEVEMENTS):
            y = 257+i*80
            done = i in self.state.achievements
            self.box((580,y,672,69))
            self.box((598,y+17,36,36),LIME if done else "#344256",10)
            self.text("+" if done else "?",616,y+34,24,"#26332c" if done else MUTED,True,True)
            self.text(title,651,y+10,20,INK,True)
            self.text(detail,651,y+38,15,MUTED)

    def prestige_panel(self):
        s = self.state
        self.box((580,183,672,562))
        self.text("NOVÁ ÉRA",616,214,14,LIME,True)
        self.text("Začni znovu. Vydělávej víc.",616,253,30,INK,True)
        self.text("Prestige vymění postup za trvalý bonus k produkci.",616,309,18,MUTED)
        self.text("Resetuje Coins, postavičky, levely a lokace.",616,344,18,MUTED)
        self.text("Achievementy a celkový výdělek ti zůstávají.",616,376,18,MUTED)
        self.text(f"Trvalý bonus: +{s.prestige*25} %",616,436,25,LIME,True)
        self.text(f"Výdělek v této éře: {compact(s.run_earned)} / {compact(PRESTIGE_COST)}",616,483,18)
        progress = min(1,s.run_earned/PRESTIGE_COST)
        self.box((616,523,592,12),"#344256",6)
        if progress:
            self.box((616,523,max(12,int(592*progress)),12),LIME,6)
        self.text(f"Získáš {s.prestige_reward} bodů · každý přidá +25 %",616,558,18,MUTED)
        self.button("Provést prestige",(616,623,592,54),lambda:setattr(self,"modal",True),s.prestige_reward>0,True)

    def ascend(self):
        if not self.state.ascend():
            return
        self.location = 0
        self.modal = False
        self.tab = "Vylepšení"
        self.selected_units = [0]*len(BRAINROTS)
        self.world = World()
        self.save()
        self.notify("Nová éra začíná! Tvůj trvalý bonus už je aktivní.")

    def draw(self):
        self.buttons = []
        self.surface.fill(BG)
        if self.view == "world":
            self.world.draw(self)
            self.present()
            return
        self.box((28,28,46,46),LIME,14)
        self.text("B",51,50,29,"#1b3023",True,True)
        self.text("BRAINROT",87,25,27,INK,True)
        self.text("B O R O U G H",88,58,13,MUTED,True)
        self.text("Z malého dvorku do celého vesmíru.",293,44,17,MUTED)
        for x,label,value,color in ((716,"COINS",compact(self.state.coins),LIME),(923,"ZA SEKUNDU",compact(self.state.income),INK),(1110,"PRESTIGE",f"+{self.state.prestige*25}%","#c0a2f1")):
            self.text(label,x,24,12,MUTED,True)
            self.text(value,x,47,29,color,True)
        pygame.draw.line(self.surface,"#2b3543",(28,94),(1252,94))
        self.button("<",(28,115,44,40),lambda:setattr(self,"location",self.location-1),self.location>0)
        self.text(f"{self.location+1:02} / {len(LOCATIONS)} · {LOCATIONS[self.location][0]}",291,135,18,INK,True,True)
        self.button(">",(510,115,44,40),lambda:setattr(self,"location",self.location+1),self.location<self.state.location)
        for i,tab in enumerate(("Vylepšení","Úspěchy","Prestige")):
            self.button(tab,(580+i*163,115,151,40),lambda tab=tab:setattr(self,"tab",tab),True,self.tab==tab)
        self.button("Zpět na mapu",(1070,115,182,40),self.close_menu)
        self.scene()
        {"Vylepšení":self.upgrades,"Úspěchy":self.milestones,"Prestige":self.prestige_panel}[self.tab]()
        if not self.save_enabled:
            self.text("POZOR: Ukládání je vypnuté. Původní save nelze načíst; oprav ho nebo použij --save s jinou cestou.",29,782,14,LIME)
        elif time.monotonic()<self.notice_until:
            self.text(self.notice,29,782,14,LIME)
        else:
            self.text("Automatické uložení každých 15 s a při ukončení · Ctrl+S uložit · Esc zavřít dialog",29,782,14,MUTED)
        for x,y,text,life in self.sparks:
            self.text(text,x,y,24,LIME,True,True)
        if self.modal:
            shade=pygame.Surface((W,H),pygame.SRCALPHA)
            shade.fill((5,10,18,215))
            self.surface.blit(shade,(0,0))
            self.buttons=[]
            self.box((330,265,620,280),"#263143")
            self.text("Připraven na novou éru?",370,299,28,INK,True)
            self.text("Coins, postavičky, levely a lokace se resetují.",370,355,18,MUTED)
            self.text(f"Získáš trvalý bonus +{self.state.prestige_reward*25} %.",370,390,20,LIME)
            self.button("Ještě ne",(370,463,240,48),lambda:setattr(self,"modal",False))
            self.button("Začít novou éru",(630,463,280,48),self.ascend,True,True)
        self.present()

    def present(self):
        scale,ox,oy=self.viewport()
        self.window.fill("#090d13")
        image=pygame.transform.smoothscale(self.surface,(max(1,int(W*scale)),max(1,int(H*scale))))
        self.window.blit(image,(int(ox),int(oy)))
        pygame.display.flip()

    def close_menu(self):
        self.modal = False
        self.view = "world"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.modal:
                    self.modal = False
                elif self.view == "menu":
                    self.close_menu()
            elif event.key == pygame.K_e and self.view == "world":
                self.world.interact(self)
            elif event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                if self.save():
                    self.notify("Hra uložena.")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect,action in reversed(self.buttons):
                if rect.collidepoint(self.mouse()):
                    action()
                    break

    def run(self, frames=0, screenshot=None):
        running=True
        count=0
        try:
            while running:
                dt=self.clock.tick(60)/1000
                self.elapsed+=dt
                self.state.tick(dt)
                self.sparks=[[x,y-35*dt,t,life-dt] for x,y,t,life in self.sparks if life>dt]
                if self.view == "world" and pygame.key.get_focused():
                    keys = pygame.key.get_pressed()
                    control = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
                    direction = (int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                                 int((keys[pygame.K_s] and not control) or keys[pygame.K_DOWN])-int(keys[pygame.K_w] or keys[pygame.K_UP]))
                    self.world.update(dt, direction, keys[pygame.K_e], self)
                self.draw()
                for event in pygame.event.get():
                    if event.type==pygame.QUIT:
                        running=False
                    else:
                        self.handle_event(event)
                if time.monotonic()-self.last_save>=15:
                    self.save()
                    self.last_save=time.monotonic()
                count+=1
                if frames and count>=frames:
                    running=False
            if screenshot:
                pygame.image.save(self.surface,screenshot)
        finally:
            if not self.smoke:
                self.save()
            pygame.quit()


def main():
    parser=argparse.ArgumentParser(description="Brainrot Borough — idle tycoon")
    parser.add_argument("--save",type=Path,help="Vlastní cesta k uložené hře")
    parser.add_argument("--smoke-test",action="store_true",help="Vykreslí několik snímků bez uložení")
    parser.add_argument("--screenshot",type=Path,help="Uloží poslední snímek do PNG")
    args=parser.parse_args()
    Game(args.save,args.smoke_test).run(5 if args.smoke_test else 0,args.screenshot)


if __name__=="__main__":
    main()
