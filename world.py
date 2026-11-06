"""Walkable north/south world, encounters, gates and the player's home plot."""
import math
import random
import time

import pygame

from game_state import BASE_SLOTS, BRAINROTS, LOCATIONS, SLOTS_PER_EXPANSION

OFFSET = 4000
WIDTH, HEIGHT = 1280, 3100 + OFFSET
HOME = pygame.Rect(250, 2490 + OFFSET, 780, 510)
SPAWN = (640, 2660 + OFFSET)
GATES = tuple((2450 + OFFSET - level*800, level) for level in range(1, len(LOCATIONS)))
THEMES = (
    ("#719e67", "#a6cd7c", "#cce690", "forest"),
    ("#6d9597", "#96b8b4", "#addbdb", "city"),
    ("#282b4b", "#55547f", "#c4a6f6", "crystal"),
    ("#316e60", "#4c9a71", "#edcf67", "jungle"),
    ("#b6d9e5", "#d8eff2", "#78b5d9", "ice"),
    ("#4d353c", "#8b4b43", "#ffab62", "lava"),
    ("#27233e", "#4f3b73", "#ef8fdb", "neon"),
    ("#b0b0d1", "#dcdaf0", "#ffe5a0", "temple"),
)
SPEED = 245
CAPTURE_TIME = 1.4
HOME_ROW_STEP = 144


class World:
    def __init__(self, plot_level=0, base_slots=BASE_SLOTS):
        self.plot_level = plot_level
        self.capacity = base_slots+plot_level*SLOTS_PER_EXPANSION
        self.columns = 4
        width = 640+plot_level*40
        height = 330+math.ceil(self.capacity/self.columns)*HOME_ROW_STEP
        self.home = pygame.Rect(640-width//2,HOME.top,width,height)
        self.height = max(HEIGHT,self.home.bottom+120)
        self.workshop = pygame.Rect(self.home.right-185,self.home.bottom-115,140,80)
        self.player = pygame.Vector2(SPAWN)
        self.camera = 0
        self.target = None
        self.progress = 0
        self.obstacles = []
        self.encounters = []
        for zone in range(len(LOCATIONS)):
            top = 1720 + OFFSET - zone*800
            for n, (x, dy) in enumerate(((330, 140), (900, 210), (430, 430), (970, 490))):
                self.encounters.append({"index": zone*2+n%2, "pos": (x, top+dy), "cooldown": 0.0})
        self.background = self.build_background()
        self.add_home_obstacles()

    @property
    def at_home(self):
        return self.home.collidepoint(self.player)

    @property
    def region(self):
        return sum(self.player.y < y for y, _ in GATES)

    def build_background(self):
        # Static terrain is drawn once; sprites and effects are rendered each frame.
        image = pygame.Surface((WIDTH,HEIGHT))
        image.fill(THEMES[-1][0])
        rng = random.Random(31)
        for zone,(ground,light,accent,motif) in enumerate(THEMES):
            top = 1650 + OFFSET - zone*800
            pygame.draw.rect(image,ground,(0,top,WIDTH,800))
            for _ in range(85):
                x,y = rng.randrange(35,1245),top+rng.randrange(30,780)
                pygame.draw.ellipse(image,light,(x,y,rng.randrange(12,45),rng.randrange(4,12)))
                if zone in (0,3):
                    for dx,dy in ((-3,0),(3,0),(0,-3),(0,3)):
                        pygame.draw.circle(image,accent,(x+dx,y+dy),2)
                    pygame.draw.circle(image,"#f8ecc2",(x,y),2)
                elif zone in (2,6,7):
                    pygame.draw.line(image,accent,(x-3,y),(x+3,y),1)
                    pygame.draw.line(image,accent,(x,y-3),(x,y+3),1)
            # A layered road with stone edges, paving and side trails.
            road = "#7e7289" if zone in (2,6) else "#bac9d2" if zone == 4 else "#cfbd91"
            pygame.draw.rect(image,"#3e4c4c",(552,top,176,800))
            pygame.draw.rect(image,road,(561,top,158,800))
            for y in range(top,top+800,40):
                pygame.draw.line(image,"#a6a4a0",(564,y),(716,y),1)
                pygame.draw.line(image,"#a6a4a0",(640+(y%80//40)*35,y),(640+(y%80//40)*35,y+40),1)
            pygame.draw.rect(image,road,(255,top+385,780,60),border_radius=22)
            # Pools / lava flows, kept off the routes to encounters.
            for x in (40,1070):
                pygame.draw.ellipse(image,"#364e59" if zone != 5 else "#f77943",(x,top+480,160,125))
                pygame.draw.ellipse(image,"#72b8bd" if zone != 5 else "#ffc26c",(x+9,top+487,140,95))
                for dy in (20,42,64):
                    pygame.draw.arc(image,"#bae2d7" if zone != 5 else "#ffe09b",(x+25,top+490+dy,95,18),0,math.pi,2)
            for n in range(12):
                x = (95,200,1075,1180)[n%4]
                y = top+125+(n//4)*235
                pygame.draw.ellipse(image,"#344a49",(x-40,y+5,91,27))
                if motif in ("forest","jungle"):
                    pygame.draw.rect(image,"#886849",(x-9,y-30,18,62),border_radius=5)
                    for dx,dy,radius in ((-24,-27,35),(22,-36,36),(0,-66,37)):
                        pygame.draw.circle(image,"#255743",(x+dx,y+dy),radius+3)
                        pygame.draw.circle(image,"#43875d" if zone==0 else "#3b936c",(x+dx,y+dy-4),radius)
                        pygame.draw.circle(image,"#69a46c",(x+dx-9,y+dy-13),radius//2)
                    if zone == 3:
                        pygame.draw.arc(image,"#f3ce66",(x-20,y-38,35,27),math.pi,math.tau,7)
                    self.obstacles.append(pygame.Rect(x-18,y-5,36,35))
                elif motif in ("city","temple","neon"):
                    rect=pygame.Rect(x-37,y-76,74,105)
                    pygame.draw.rect(image,"#344252",rect.inflate(7,7),border_radius=9)
                    pygame.draw.rect(image,light,rect,border_radius=7)
                    pygame.draw.rect(image,accent,(x-42,y-85,84,22),border_radius=5)
                    for dx in (-22,9):
                        for dy in (-48,-16):
                            pygame.draw.rect(image,"#374d62",(x+dx,y+dy,16,22),border_radius=3)
                            pygame.draw.line(image,accent,(x+dx+3,y+dy+4),(x+dx+3,y+dy+17),3)
                    if zone==7:
                        pygame.draw.polygon(image,"#fff0c4",[(x-46,y-84),(x,y-121),(x+46,y-84)])
                    self.obstacles.append(rect)
                else:
                    pygame.draw.polygon(image,"#324153",[(x-29,y+25),(x-38,y-15),(x,y-82),(x+34,y-12),(x+24,y+25)])
                    pygame.draw.polygon(image,accent,[(x-25,y+18),(x-30,y-18),(x,y-76),(x+28,y-13),(x+20,y+18)])
                    pygame.draw.polygon(image,light,[(x,y-76),(x-2,y+15),(x+28,y-13)])
                    pygame.draw.line(image,"#f9eada",(x,y-65),(x-20,y-13),2)
                    self.obstacles.append(pygame.Rect(x-25,y-10,50,35))
        pygame.draw.rect(image,"#86aa6c",(0,OFFSET+2450,WIDTH,HEIGHT-(OFFSET+2450)))
        return image

    def add_home_obstacles(self):
        h = self.home
        for start,end in (((h.left,h.top),(550,h.top)),((730,h.top),(h.right,h.top)),
                          ((h.left,h.top),(h.left,h.bottom)),((h.right,h.top),(h.right,h.bottom)),
                          ((h.left,h.bottom),(h.right,h.bottom))):
            self.obstacles.append(pygame.Rect(min(start[0],end[0])-4,min(start[1],end[1])-4,
                                              abs(end[0]-start[0])+8,abs(end[1]-start[1])+8))
        self.obstacles.append(self.workshop.copy())

    def home_position(self,slot):
        row,col = divmod(slot,self.columns)
        pitch = 124+self.plot_level*6
        x = (640-96-pitch,640-96,640+96,640+96+pitch)[col]
        return x,self.home.top+150+row*HOME_ROW_STEP

    def visible_home_slots(self):
        first_row = max(0,int((self.camera-self.home.top-240)//HOME_ROW_STEP))
        last_row = max(0,int((self.camera+820-self.home.top+50)//HOME_ROW_STEP)+1)
        return range(first_row*self.columns,min(self.capacity,last_row*self.columns))

    def home_units(self,state):
        """One actor per individual; skip rows outside the camera before enumerating."""
        slots = self.visible_home_slots()
        offset = 0
        for species,amount in enumerate(state.owned):
            start = max(0,slots.start-offset)
            stop = min(amount,slots.stop-offset)
            for unit in range(start,stop):
                x,y = self.home_position(offset+unit)
                yield species,unit,x,y
            offset += amount

    def draw_home(self,game):
        cy,h = self.camera,self.home
        if h.bottom < cy or h.top > cy+820:
            return
        # Draw only the viewport, even for very large migrated collections.
        game.box((h.x-10,h.y-cy-10,h.width+20,h.height+20),"#527d56",20)
        game.box((h.x,h.y-cy,h.width,h.height),"#a5bf7e",14)
        pygame.draw.rect(game.surface,"#d4c797",(607,h.top-cy,66,h.height-35))
        pygame.draw.rect(game.surface,"#dacfac",(562,OFFSET+2450-cy,156,h.top-(OFFSET+2450)+6))
        for start,end in (((h.left,h.top),(550,h.top)),((730,h.top),(h.right,h.top)),
                          ((h.left,h.top),(h.left,h.bottom)),((h.right,h.top),(h.right,h.bottom)),
                          ((h.left,h.bottom),(h.right,h.bottom))):
            pygame.draw.line(game.surface,"#ecddbb",(start[0],start[1]-cy),(end[0],end[1]-cy),7)
        for y in range(max(h.top+12,int(cy)//28*28),min(h.bottom,int(cy)+848),28):
            for x in (h.left,h.right):
                game.box((x-6,y-cy-4,12,17),"#f6e6be",3)
        for slot in self.visible_home_slots():
            x,y = self.home_position(slot)
            pygame.draw.ellipse(game.surface,"#6e8c5c",(x-47,y-cy-4,94,38))
            pygame.draw.ellipse(game.surface,"#d3d4a0",(x-43,y-cy-9,86,34))
            pygame.draw.ellipse(game.surface,"#a7c784",(x-35,y-cy-8,70,24))
        r = self.workshop.move(0,-cy)
        if r.bottom > -100 and r.top < 920:
            pygame.draw.ellipse(game.surface,"#6c8a53",r.inflate(25,25))
            game.box(r,"#f1ddad",7)
            pygame.draw.polygon(game.surface,"#b97056",[(r.left-16,r.top+3),(r.centerx,r.top-55),(r.right+16,r.top+3)])
            game.box((r.x+36,r.y+25,38,55),"#4a675c",5)
            game.box((r.x+94,r.y+21,25,26),"#78b8c7",3)
            pygame.draw.line(game.surface,"#f8ebc3",(r.x+106,r.y+21),(r.x+106,r.y+47),2)
        game.text(f"POZEMEK Lv {self.plot_level+1} · {self.capacity} míst",640,h.top+45-cy,23,"#f0f1cf",True,True)

    def nearest(self, state):
        candidates = [(self.player.distance_to(e["pos"]), i) for i,e in enumerate(self.encounters)
                      if e["cooldown"] <= 0 and BRAINROTS[e["index"]].location <= state.location]
        if not candidates:
            return None
        distance, index = min(candidates)
        return index if distance <= 92 else None

    def blocked(self, point, state):
        if not 35 <= point.x <= WIDTH-35 or not 60 <= point.y <= self.height-35:
            return True
        if any(point.y < y+23 and state.location < level for y,level in GATES):
            return True
        body = pygame.Rect(point.x-15, point.y-12, 30, 24)
        return any(body.colliderect(rect) for rect in self.obstacles)

    def update(self, dt, direction, holding, game):
        state = game.state
        dt = min(dt, .05)
        for encounter in self.encounters:
            encounter["cooldown"] = max(0, encounter["cooldown"]-dt)
        direction = pygame.Vector2(direction)
        if direction.length_squared():
            direction = direction.normalize()*SPEED*dt
            for axis in (0,1):
                candidate = self.player.copy()
                candidate[axis] += direction[axis]
                if not self.blocked(candidate, state):
                    self.player = candidate
        if self.at_home and state.cargo is not None:
            name = BRAINROTS[state.cargo].name
            if state.deposit():
                game.notify(f"{name} je na pozemku a vydělává Coins!")
                game.save()
        target = self.nearest(state) if state.cargo is None else None
        if target != self.target or not holding or direction.length_squared():
            self.progress = 0
        self.target = target
        if state.used_slots >= state.capacity:
            self.progress = 0
        if target is not None and holding and not direction.length_squared() and state.used_slots < state.capacity:
            self.progress += dt
            if self.progress >= CAPTURE_TIME:
                encounter = self.encounters[target]
                if state.capture(encounter["index"]):
                    encounter["cooldown"] = 25
                    game.notify("Chyceno! Dones Brainrota na svůj pozemek směrem na jih.")
                    game.save()
                else:
                    game.notify("Nemáš volný slot. Prodej Brainrota nebo rozšiř pozemek.")
                self.progress = 0

    def interact(self, game):
        if self.at_home:
            game.view = "menu"
            return
        for y, level in GATES:
            if game.state.location == level-1 and abs(self.player.y-(y+30)) < 115:
                if game.state.unlock():
                    game.location = game.state.location
                    game.notify(f"Brána otevřena: {LOCATIONS[level][0]}!")
                    game.save()
                else:
                    game.notify(f"Na otevření brány potřebuješ {LOCATIONS[level][1]:,} Coins.")
                return
        if self.nearest(game.state) is not None and game.state.used_slots >= game.state.capacity:
            game.notify("Pozemek je plný. Doma prodej Brainrota nebo kup rozšíření.")

    def draw(self, game):
        state = game.state
        self.camera = max(0,min(self.height-820,self.player.y-440))
        cy = self.camera
        surface = game.surface
        surface.fill("#86aa6c")
        surface.blit(self.background,(0,-int(cy)))
        self.draw_home(game)
        # Region labels on the ground.
        labels = [(name.upper(),1810+OFFSET-zone*800) for zone,(name,_) in enumerate(LOCATIONS)]
        for title,y in labels:
            if -50 < y-cy < 820:
                game.text(title,640,y-cy,25,"#e5edcd",True,True)
        for y,level in GATES:
            locked = state.location < level
            if -60 < y-cy < 900:
                pygame.draw.rect(surface,"#4f6357",(0,y-cy-8,WIDTH,16))
                pygame.draw.rect(surface,"#d3bb82",(540,y-cy-20,200,40),border_radius=7)
                if locked:
                    game.box((415,y-cy-26,450,56),"#27323e",10)
                    game.text(f"E · Odemknout sever za {LOCATIONS[level][1]:,} Coins",640,y-cy+1,18,"#f6d890",True,True)
                else:
                    pygame.draw.rect(surface,"#dacfac",(562,y-cy-20,156,40))
        actors = []
        for i,e in enumerate(self.encounters):
            if e["cooldown"] <= 0 and BRAINROTS[e["index"]].location <= state.location:
                actors.append((e["pos"][1], "wild", i))
        for species,unit,x,y in self.home_units(state):
            actors.append((y,"home",(species,unit,x)))
        actors.append((self.player.y,"player",None))
        for y,kind,data in sorted(actors, key=lambda a:a[0]):
            if not -120 < y-cy < 920:
                continue
            if kind == "player":
                x = self.player.x
                py = self.player.y-cy
                pygame.draw.ellipse(surface,"#42554a",(x-21,py+5,42,16))
                stride = math.sin(game.elapsed*12)*5 if pygame.key.get_focused() and any(pygame.key.get_pressed()[k] for k in (pygame.K_w,pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT)) else 0
                pygame.draw.line(surface,"#293c51",(x-9,py-6),(x-11,py+8+stride),8)
                pygame.draw.line(surface,"#293c51",(x+9,py-6),(x+11,py+8-stride),8)
                game.box((x-19,py-36,38,34),"#e5f58d",10)
                game.box((x-16,py-34,10,25),"#f5ffbf",5)
                pygame.draw.line(surface,"#e9bb96",(x-21,py-29),(x-25,py-10),7)
                pygame.draw.line(surface,"#e9bb96",(x+21,py-29),(x+25,py-10),7)
                pygame.draw.circle(surface,"#f2c49e",(int(x),int(py-48)),17)
                pygame.draw.arc(surface,"#243e45",(x-19,py-68,38,32),0,math.pi,10)
                pygame.draw.circle(surface,"#263341",(int(x-6),int(py-48)),2)
                pygame.draw.circle(surface,"#263341",(int(x+6),int(py-48)),2)
                if state.cargo is not None:
                    b = BRAINROTS[state.cargo]
                    game.character(x+34,py-22,b.shape,b.color,.38)
            else:
                if kind == "wild":
                    e = self.encounters[data]
                    i,x = e["index"],e["pos"][0]
                else:
                    i,unit,x = data
                b = BRAINROTS[i]
                if kind == "wild" and self.target == data and state.cargo is None:
                    pygame.draw.ellipse(surface,"#e0fa99",(x-49,y-cy+20,98,29),3)
                game.character(x,y-cy-18,b.shape,b.color,.68,math.sin(game.elapsed*2+x)*4)
                if kind == "wild":
                    game.box((x-142,y-cy-96,284,27),"#24323d",8)
                    game.text(b.name,x,y-cy-83,14,"#f5f1de",True,True)
                else:
                    game.box((x-54,y-cy+33,108,23),"#24323d",7)
                    game.text(f"#{unit+1} · Lv {state.levels[i][unit]}",x,y-cy+44,14,"#f5f1de",True,True)
                if kind == "wild":
                    game.text(b.rarity,x,y-cy+44,12,"#fff2c7",True,True)
        # Fixed HUD; the map continues behind it.
        game.box((20,18,905,83),"#19282b",16)
        game.text("BRAINROT BOROUGH",40,29,22,"#e2f5c4",True)
        game.text("Tvůj pozemek" if self.at_home else LOCATIONS[self.region][0],40,63,17,"#afc7b4")
        game.text(f"{self.short(state.coins)} Coins",410,32,24,"#d3f878",True)
        game.text(f"Produkce {self.short(state.income)} / s",680,37,18,"#eaf0dd")
        game.text(f"Sloty {state.used_slots} / {state.capacity}",680,67,14,"#efb2a0" if state.used_slots>=state.capacity else "#afc7b4")
        game.button("Správa pozemku · E",(950,24,306,58),lambda:self.interact(game),self.at_home,True)
        # Small north-up minimap with player position and home marker.
        game.box((1133,111,123,205),"#19282b",12)
        for zone,theme in enumerate(THEMES):
            top = 122+(1650+OFFSET-zone*800)/self.height*182
            pygame.draw.rect(surface,theme[1],(1145,top,98,800/self.height*182+1))
        pygame.draw.rect(surface,"#adc589",(1145,122+self.home.top/self.height*182,98,self.home.height/self.height*182))
        pygame.draw.line(surface,"#dfd5af",(1194,124),(1194,301),3)
        pygame.draw.circle(surface,"#ffffff",(int(1145+self.player.x/WIDTH*98),int(122+self.player.y/self.height*182)),5)
        game.text("N",1194,123,13,"#f5f4d9",True,True)
        context = "WASD / šipky · Vydej se na sever a hledej Brainroty."
        if state.cargo is not None:
            context = f"Neseš {BRAINROTS[state.cargo].name}. Vrať se na pozemek na jihu ↓"
        elif self.at_home:
            context = "Tvůj pozemek · E otevře správu · Na lov vyraz směrem na sever ↑"
        elif self.target is not None:
            context = "Pozemek je plný. Doma prodej Brainrota nebo kup rozšíření." if state.used_slots>=state.capacity else "Podrž E a nehýbej se: chyť Brainrota. Potom ho dones domů."
        else:
            for y,level in GATES:
                if state.location == level-1 and abs(self.player.y-(y+30))<115:
                    context = f"E · Otevřít bránu do {LOCATIONS[level][0]} za {LOCATIONS[level][1]:,} Coins"
        game.box((20,691,1095,109),"#19282b",14)
        game.text(context,40,708,19,"#e1f0ce",True)
        game.text("WASD / šipky: pohyb   ·   E: interakce / držet pro chycení   ·   Ctrl+S: uložit",40,741,16,"#a8bdb0")
        if self.progress:
            game.box((40,775,1020,7),"#3c534b",3)
            game.box((40,775,max(7,int(1020*self.progress/CAPTURE_TIME)),7),"#d3f878",3)
        if not game.save_enabled:
            game.text("Ukládání vypnuto: původní save nelze načíst.",40,769,15,"#ffcb8d")
        elif game.notice_until > time.monotonic() and not self.progress:
            game.text(game.notice,40,769,15,"#d3f878")

    @staticmethod
    def short(value):
        for divisor,suffix in ((1e12,"T"),(1e9,"B"),(1e6,"M"),(1e3,"k")):
            if value >= divisor:
                return f"{value/divisor:.1f}{suffix}"
        return f"{value:.0f}"
