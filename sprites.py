"""Original character artwork, rendered at high resolution and cached by the game."""
import math

import pygame

OUTLINE = "#273342"


def render_character(kind, color, size):
    image = pygame.Surface((540,540),pygame.SRCALPHA)
    scale, origin = 3, 270

    def point(p):
        return (round(origin+p[0]*scale),round(origin+p[1]*scale))

    def ellipse(c,r,outline=True):
        rect=pygame.Rect(round(origin+r[0]*scale),round(origin+r[1]*scale),round(r[2]*scale),round(r[3]*scale))
        pygame.draw.ellipse(image,c,rect)
        if outline:
            pygame.draw.ellipse(image,OUTLINE,rect,5)

    def poly(c,points,outline=True):
        pts=[point(p) for p in points]
        pygame.draw.polygon(image,c,pts)
        if outline:
            pygame.draw.lines(image,OUTLINE,True,pts,5)

    def line(c,a,b,w=2):
        pygame.draw.line(image,c,point(a),point(b),max(1,round(w*scale)))

    def rect(c,r,radius=6):
        target=pygame.Rect(round(origin+r[0]*scale),round(origin+r[1]*scale),round(r[2]*scale),round(r[3]*scale))
        pygame.draw.rect(image,c,target,border_radius=radius*scale)
        pygame.draw.rect(image,OUTLINE,target,5,border_radius=radius*scale)

    def eye(x,y,r=8,sleepy=False):
        ellipse("#fffaf0",(x-r,y-r,r*2,r*2+2))
        ellipse("#253542",(x-1,y-3,6,10),False)
        ellipse("#ffffff",(x,y-4,2.5,3),False)
        if sleepy:
            line(OUTLINE,(x-r,y-3),(x+r,y-3),3)

    def smile(x,y,w=17):
        target=(origin+(x-w/2)*scale,origin+y*scale,w*scale,10*scale)
        pygame.draw.arc(image,OUTLINE,target,math.pi,math.tau,5)

    def sneaker(x,y,c="#5c9ce5",s=1):
        ellipse(c,(x-14*s,y-5*s,29*s,14*s))
        line("#f5f2e9",(x-12*s,y+5*s),(x+12*s,y+5*s),3)
        for a in (-4,1,6):
            line("#f5f2e9",(x+a*s,y-2*s),(x+(a-2)*s,y+1*s),1.4)

    ellipse((12,22,31,65),(-49,48,100,17),False)
    if kind=="log":
        line(OUTLINE,(-24,-5),(-43,22),10)
        line("#ae794d",(-24,-5),(-43,22),7)
        line(OUTLINE,(25,-4),(47,13),10)
        line("#bc8a59",(25,-4),(47,13),7)
        rect("#987044",(-28,-57,56,105),15)
        rect(color,(-24,-54,47,100),12)
        ellipse("#e5bd87",(-26,-60,53,19))
        for inset in (6,13):
            pygame.draw.ellipse(image,"#a5794c",(origin+(-26+inset)*scale,origin+(-59+inset/3)*scale,(53-inset*2)*scale,(17-inset/2)*scale),3)
        for x in (-19,-8,8,18):
            line("#b48753",(x,-35),(x-2,39),1.2)
        ellipse("#986940",(-12,19,9,14),False)
        ellipse("#c69a65",(-10,21,5,9),False)
        line("#ebc996",(-21,-32),(-21,31),2)
        eye(-11,-20,9); eye(11,-20,9)
        line(OUTLINE,(-20,-34),(-4,-30),2)
        line(OUTLINE,(5,-30),(20,-34),2)
        poly("#b47c50",[(-3,-10),(4,0),(-3,1)])
        smile(0,6,23)
        line("#80583e",(-14,44),(-20,56),7)
        line("#80583e",(13,44),(18,56),7)
        ellipse("#ae7d50",(-32,51,24,10)); ellipse("#ae7d50",(8,51,24,10))
        poly("#825434",[(45,-43),(55,-43),(54,20),(46,20)])
        line("#bd8b54",(48,-39),(48,5),2)
        ellipse("#dab180",(40,7,16,13))
    elif kind=="shark":
        poly("#4e88b7",[(-36,0),(-76,-23),(-67,9),(-77,29),(-35,21)])
        poly("#477aa6",[(-5,-28),(7,-65),(29,-25)])
        ellipse("#5997c6",(-49,-34,112,76))
        ellipse(color,(-43,-30,101,63),False)
        ellipse("#e4ecda",(-27,3,87,32),False)
        poly("#75b4dc",[(-17,8),(-34,40),(8,19)])
        eye(28,-15,9)
        line(OUTLINE,(36,5),(60,0),2)
        for x in (38,46,54):
            poly("#fffcec",[(x,5),(x+5,3),(x+3,12)],False)
        for x in (-20,-11,-2):
            line("#386e97",(x,-14),(x-2,0),2)
        for x,y in ((-25,42),(10,47),(42,40)):
            line("#48779d",(x,28),(x,y),7)
            sneaker(x,y+6)
    elif kind=="tree":
        for x,y,r in ((-31,-39,25),(0,-57,30),(31,-40,26),(-22,-15,23),(25,-11,23)):
            ellipse("#477b4c",(x-r,y-r,r*2,r*2))
            ellipse(color,(x-r+5,y-r+3,r*1.4,r*1.1),False)
        poly("#9b704d",[(-19,-21),(19,-22),(25,37),(43,50),(12,49),(0,40),(-18,51),(-46,49),(-25,34)])
        ellipse("#e2bf8b",(-22,-24,46,54))
        eye(-11,-12,7); eye(11,-12,7)
        ellipse("#b88b60",(-4,-3,35,18))
        smile(-5,15,15)
        for a in (-31,-20,18,30):
            line("#d3aa79",(a,41),(a-3,48),2)
    elif kind=="cup":
        line("#e7b1c7",(-17,9),(-45,-7),5); line("#e7b1c7",(17,9),(46,-9),5)
        ellipse("#e9c3aa",(18,-40,37,38)); ellipse("#273342",(27,-32,18,22))
        poly("#f7e4cb",[(-32,-43),(30,-43),(23,11),(-22,11)])
        ellipse("#b48463",(-31,-49,62,20))
        ellipse("#f5d5aa",(-22,-45,43,12),False)
        for x in (-9,5):
            ellipse("#fff1d5",(x,-43,13,8),False)
        poly("#fff1d5",[(-8,-38),(15,-38),(3,-32)],False)
        eye(-12,-23,7); eye(11,-23,7)
        smile(0,-8,13)
        poly(color,[(-15,10),(15,10),(48,32),(20,41),(0,34),(-23,41),(-48,32)])
        for x in (-28,-12,12,28):
            line("#c879a6",(x/2,14),(x,34),1.4)
        for x in (-12,12):
            line("#d88baa",(x,35),(x+(-4 if x<0 else 4),53),4)
            ellipse("#efb6d1",(x-9,51,22,8))
        line("#d6e6e0",(-11,-58),(-16,-67),2); line("#d6e6e0",(8,-58),(13,-70),2)
    elif kind=="croc":
        poly("#758c6c",[(-16,-14),(-3,-60),(13,-58),(18,-9),(66,34),(5,23),(-52,37)])
        poly("#b7c69d",[(-8,-9),(61,30),(8,15),(-48,31)])
        ellipse("#71966b",(-61,-24,117,57))
        poly("#8eae74",[(-66,-7),(-52,-31),(33,-24),(68,-6),(66,16),(-53,20)])
        eye(22,-26,9); eye(42,-23,8)
        line("#3d634d",(-44,7),(62,5),3)
        for x in range(-34,55,13):
            poly("#f9f0c9",[(x,7),(x+8,7),(x+4,17)],False)
        for x in (-40,-25,-10):
            ellipse("#4d714e",(x,-17,7,5),False)
        line(OUTLINE,(-67,-22),(-67,30),4); ellipse("#d7c799",(-74,-4,14,13))
        ellipse("#263542",(-30,28,16,17)); ellipse("#263542",(27,27,16,17))
    elif kind=="planet":
        ellipse("#ae8cd0",(-42,-44,84,88))
        ellipse("#efe5fa",(-35,-42,64,76),False)
        for x,y,w,h in ((-29,-33,21,27),(10,-9,22,28),(-15,20,23,16)):
            ellipse("#8368ad",(x,y,w,h),False)
        for side in (-1,1):
            poly("#dfb98b",[(side*19,-39),(side*35,-60),(side*33,-32)])
            ellipse("#c09be0",(side*34-12,-34,24,17))
            line("#81669f",(side*19,38),(side*23,52),7)
            ellipse("#48415e",(side*23-9,48,20,10))
        eye(-14,-18,8); eye(14,-18,8)
        ellipse("#e9b6cb",(-24,-2,48,26))
        for x in (-11,8): ellipse("#8d657c",(x,5,5,8),False)
        pygame.draw.arc(image,"#f4d78e",(origin-72*scale,origin-11*scale,144*scale,43*scale),math.pi,math.tau,17)
        ellipse("#f2ddac",(52,-18,10,10),False)
    elif kind=="banana":
        poly("#c49f37",[(-41,40),(-50,-25),(-25,-63),(-15,-21),(12,16),(42,28),(26,49)])
        poly(color,[(-37,35),(-44,-24),(-26,-51),(-20,-15),(10,22),(35,30),(22,42)])
        ellipse("#785037",(-27,-24,55,65))
        for x in (-34,21): ellipse("#b18656",(x,-35,18,24))
        ellipse("#875a3b",(-27,-45,55,51))
        ellipse("#e6bf8c",(-22,-38,45,39),False)
        ellipse("#e6bf8c",(-14,-12,28,22),False)
        eye(-11,-28,7); eye(11,-28,7); smile(0,-6)
        for x in (-23,22):
            line("#875a3b",(x,0),(x*1.5,28),9)
            ellipse("#d6ad7c",(x*1.5-7,23,15,14))
        for x in (-13,13): ellipse("#b68a5f",(x-10,43,22,13))
    elif kind=="dolphin":
        poly("#e0bf54",[(-21,33),(-59,52),(-41,22),(-58,11),(-24,15)])
        poly("#79bcc8",[(-13,-15),(-16,-60),(11,-31)])
        ellipse("#69b2c0",(-39,-31,83,68))
        ellipse(color,(-31,-29,69,55),False)
        ellipse("#bce9d9",(-21,2,52,24),False)
        poly(color,[(22,-14),(65,-3),(63,9),(28,11)])
        poly("#69b2c0",[(-1,7),(-26,39),(17,20)])
        eye(22,-19,8); smile(48,2,17)
        for x in (-9,18): sneaker(x,49,"#e8ce62",.8)
    elif kind=="fridge":
        for x in (-29,-9,13,32):
            line("#be9974",(x,24),(x,49),6); ellipse("#785e49",(x-6,46,15,9))
        rect("#e6eef0",(-38,-29,72,59),7)
        line("#7fa4b6",(-35,-7),(31,-7),2)
        line("#8c9eae",(21,3),(21,18),3)
        poly("#d5b793",[(22,-19),(29,-56),(42,-59),(47,-8),(33,10)])
        ellipse("#e4c9a1",(22,-67,48,25))
        poly("#b79a72",[(29,-61),(24,-76),(37,-66)])
        eye(45,-58,5); ellipse("#997856",(61,-59,6,5),False)
        for x in (-30,-10,10):
            line("#88bbd4",(x,-22),(x+6,-15),2)
        rect("#94c5d6",(-28,1,29,15),3)
        line("#e6f6f7",(-24,5),(-7,5),2)
    elif kind=="penguin":
        for x in (-21,16): ellipse("#e5ad55",(x-13,45,29,13))
        ellipse("#293b50",(-34,-54,68,105))
        ellipse("#eee6cf",(-25,-26,50,72),False)
        for side in (-1,1):
            poly("#334b5d",[(side*26,-13),(side*52,26),(side*29,20)])
        eye(-12,-28,8); eye(12,-28,8)
        poly("#f2b655",[(-10,-11),(11,-11),(0,2)])
        ellipse("#805d42",(-30,10,60,33))
        ellipse("#f1dfb6",(-26,9,52,14))
        for x in (-17,0,17): line("#ab8357",(x,26),(x+4,37),1.4)
        poly("#8ac9be",[(-8,-53),(-26,-68),(-3,-63),(4,-78),(12,-60),(31,-66),(15,-51)])
    elif kind=="dragon":
        for side in (-1,1):
            poly("#854d4b",[(side*22,-14),(side*72,-57),(side*61,16),(side*34,4)])
            poly("#db7764",[(side*23,-12),(side*65,-46),(side*56,7),(side*38,-3)])
            for yy in (-40,-14,8): line("#a34f4b",(side*24,-9),(side*60,yy),2)
        ellipse("#ba6c4f",(-27,-27,54,74))
        ellipse("#f3c98c",(-19,-3,38,47))
        for yy in (7,18,29): line("#cb9867",(-16,yy),(16,yy),2)
        poly("#f2de9e",[(-23,-36),(-32,-68),(-10,-48)])
        poly("#f2de9e",[(23,-36),(32,-68),(10,-48)])
        ellipse(color,(-31,-51,63,54)); eye(-14,-35,8); eye(12,-35,8)
        ellipse("#efb47c",(-24,-16,49,23)); smile(0,-6,22)
        for x in (-13,9): ellipse("#8a5d4c",(x,-11,5,4),False)
        for side in (-1,1):
            ellipse(color,(side*22-12,36,25,17))
            for n in range(3): line("#f1dfa9",(side*22-5+n*5,46),(side*22-5+n*5,51),2)
    elif kind=="cactus":
        for side in (-1,1):
            poly("#51885c",[(side*25,12),(side*51,12),(side*54,-29),(side*39,-29),(side*37,-3),(side*25,-3)])
        ellipse("#57835b",(-35,-43,70,91)); ellipse(color,(-29,-42,58,85),False)
        for x in (-19,0,19): line("#75a56b",(x,-32),(x,34),2)
        for x in (-26,25):
            for yy in (-26,0,26): line("#efe2b6",(x,yy),(x+(-6 if x<0 else 6),yy-4),2)
        eye(-13,-22,7); eye(13,-22,7)
        ellipse("#bbd99c",(-32,-1,65,35)); smile(0,15,21)
        for x in (-19,13): ellipse("#649663",(x,6,8,6),False)
        for x in (-18,16): ellipse("#608b61",(x-11,40,24,15))
        for dx,dy in ((-9,-52),(3,-60),(13,-49),(0,-42)):
            ellipse("#ee9bb7",(dx-8,dy-8,16,16))
        ellipse("#f4d77f",(-3,-54,11,11),False)
    elif kind=="capybara":
        for x in (-29,-6,19,37):
            rect("#a77f73",(x-6,25,13,25),5)
        ellipse("#b68a81",(-48,-25,97,64)); ellipse(color,(-45,-24,88,52),False)
        ellipse("#cca398",(6,-45,57,53))
        for x in (14,39): ellipse("#ca9b91",(x,-52,17,19))
        ellipse("#e4b7a3",(31,-20,39,28))
        ellipse("#684c50",(56,-13,12,8),False)
        rect("#283b53",(11,-33,22,15),4); rect("#283b53",(37,-33,22,15),4)
        line("#e9a8f4",(14,-29),(26,-29),3); line("#e9a8f4",(41,-29),(53,-29),3)
        line("#283b53",(32,-29),(38,-29),3)
        poly("#88e4da",[(-24,-31),(-13,-45),(0,-32),(12,-40),(10,-25),(-24,-25)])
    elif kind=="axolotl":
        poly("#bd9edc",[(-19,28),(-49,48),(-65,32),(-58,9),(-39,21)])
        ellipse("#a88acb",(-23,-5,46,55))
        for side in (-1,1):
            for yy in (-42,-23,-4):
                line(OUTLINE,(side*25,yy),(side*55,yy-7),8)
                line("#ed9ccc",(side*25,yy),(side*55,yy-7),5)
                line("#f8c2e0",(side*47,yy-5),(side*52,yy-14),3)
            ellipse(color,(side*19-8,39,19,15))
        ellipse(color,(-38,-51,76,59))
        eye(-17,-28,7); eye(17,-28,7); smile(0,-12,18)
        for x in (-26,20): ellipse("#eeaecf",(x,-14,9,6),False)
        ellipse("#d8e4f0",(-14,-76,28,28))
        for x in (-8,0,8): line("#8495ba",(x,-72),(x,-53),1)
        for yy in (-69,-62,-55): line("#8495ba",(-10,yy),(10,yy),1)
    else:
        if kind=="angel":
            for side in (-1,1):
                for n in range(4):
                    ellipse("#fbf1d6",(side*(38+n*6)-12,-45+n*13,25,42))
            pygame.draw.ellipse(image,"#f5d887",(origin-26*scale,origin-73*scale,52*scale,14*scale),9)
        else:
            poly("#885278",[(-22,-20),(-47,43),(-13,50),(1,38),(23,50),(48,43),(23,-20)])
            line("#f4d785",(54,-22),(54,49),4)
            ellipse("#f3cb70",(44,-40,20,23)); ellipse("#f1a4ae",(48,-36,12,14),False)
        ellipse("#cda66b",(-29,-23,59,69)); ellipse(color,(-25,-25,50,64),False)
        eye(-12,-8,8); eye(12,-8,8); smile(0,10,20)
        if kind=="king":
            poly("#dcad54",[(-28,-28),(-35,-61),(-16,-46),(0,-69),(16,-46),(35,-61),(28,-28)])
            rect("#f0d286",(-28,-32,56,10),2)
            for x in (-18,0,18): ellipse("#ef9b9a",(x-3,-30,6,6),False)
        else:
            poly("#f7d68d",[(-5,-28),(0,-42),(5,-28),(19,-25),(7,-18),(10,-4),(0,-12),(-10,-4),(-7,-18),(-19,-25)])
        for x in (-15,15): ellipse("#d6b278",(x-11,43,23,12))
    side=max(1,round(180*size))
    return pygame.transform.smoothscale(image,(side,side))
