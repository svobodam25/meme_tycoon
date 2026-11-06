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
from inventory import Inventory
from sprites import render_character

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
        self.tab = "Inventář"
        self.inventory = Inventory()
        self.sprite_cache = {}
        self.location = self.state.location
        self.buttons = []
        self.modal = False
        self.pending_sale = None
        self.last_save = time.monotonic()
        self.sparks = []
        self.elapsed = 0
        self.view = "world"
        self.world = World(self.state.plot_level,self.state.base_slots)

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

    def expand_plot(self):
        if self.state.expand_plot():
            # Preserve exploration state while rebuilding only the home geometry.
            previous = self.world
            self.world = World(self.state.plot_level,self.state.base_slots)
            self.world.player = previous.player
            self.world.encounters = previous.encounters
            self.save()
            self.notify(f"Pozemek rozšířen! Kapacita je nyní {self.state.capacity} slotů.")

    def request_sale(self, species, unit):
        if self.state.sell_price(species,unit):
            self.pending_sale = (species,unit)
            self.modal = "sell"

    def confirm_sale(self):
        if self.pending_sale is not None:
            species,unit = self.pending_sale
            price = self.state.sell_price(species,unit)
            if self.state.sell(species,unit):
                self.inventory.selected = None
                self.inventory.clamp(self.state)
                self.save()
                self.notify(f"Brainrot prodán za {compact(price)} Coins. Slot je volný.")
        self.pending_sale = None
        self.modal = False

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
            self.sprite_cache[key] = render_character(kind,color,size)
        sprite = self.sprite_cache[key]
        self.surface.blit(sprite,sprite.get_rect(center=(round(x),round(y+bounce))))

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
        self.text("Úspěchy, celkový výdělek i pozemek ti zůstávají.",616,376,18,MUTED)
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
        self.tab = "Inventář"
        self.inventory = Inventory()
        self.world = World(self.state.plot_level,self.state.base_slots)
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
        if self.tab == "Inventář":
            self.text("SBÍRKA · VŠECHNY LOKACE",28,125,18,MUTED,True)
        else:
            self.button("<",(28,115,44,40),lambda:setattr(self,"location",self.location-1),self.location>0)
            self.text(f"{self.location+1:02} / {len(LOCATIONS)} · {LOCATIONS[self.location][0]}",291,135,18,INK,True,True)
            self.button(">",(510,115,44,40),lambda:setattr(self,"location",self.location+1),self.location<self.state.location)
        for i,tab in enumerate(("Inventář","Úspěchy","Prestige")):
            self.button(tab,(580+i*163,115,151,40),lambda tab=tab:setattr(self,"tab",tab),True,self.tab==tab)
        self.button("Zpět na mapu",(1070,115,182,40),self.close_menu)
        if self.tab == "Inventář":
            self.inventory.draw(self)
        else:
            self.scene()
            {"Úspěchy":self.milestones,"Prestige":self.prestige_panel}[self.tab]()
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
            if self.modal == "sell":
                species,unit = self.pending_sale
                self.text("Prodat tohoto Brainrota?",370,299,28,INK,True)
                self.text(f"{BRAINROTS[species].name} #{unit+1} · Lv {self.state.levels[species][unit]}",370,351,18,INK)
                self.text(f"Získáš {compact(self.state.sell_price(species,unit))} Coins a uvolníš 1 slot.",370,390,20,LIME)
                self.text("Postavička i její vylepšení budou odstraněny.",370,423,16,MUTED)
            else:
                self.text("Připraven na novou éru?",370,299,28,INK,True)
                self.text("Coins, postavičky, levely a lokace se resetují.",370,355,18,MUTED)
                self.text(f"Získáš trvalý bonus +{self.state.prestige_reward*25} %.",370,390,20,LIME)
            self.button("Ještě ne",(370,463,240,48),lambda:setattr(self,"modal",False))
            self.button("Prodat" if self.modal == "sell" else "Začít novou éru",(630,463,280,48),self.confirm_sale if self.modal == "sell" else self.ascend,True,True)
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
        if self.view == "menu" and self.tab == "Inventář" and not self.modal:
            self.inventory.handle_event(self,event)
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
