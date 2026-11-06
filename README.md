# Brainrot Borough

2D idle tycoon v Pythonu a Pygame. Prozkoumávej mapu, chytej Brainroty, nos je na vlastní pozemek a jejich výdělek investuj do jednotlivých postaviček a nových oblastí. Hra má 8 oblastí, 16 druhů Brainrotů, prestige, achievementy a automatické ukládání. Grafika je kreslená přímo v Pygame.

## Spuštění hry Brainrot Borough

Implementace používá Python 3.10+ a Pygame. Spuštění v PowerShellu:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Pokud už `.venv` existuje a Pygame je nainstalovaný, stačí poslední příkaz. Ve VS Code vyber interpreter `.venv\Scripts\python.exe`. Na Linuxu/macOS použij `.venv/bin/python`.

## Mapa a ovládání

- Začínáš se 100 Coins na vlastním oploceném pozemku. **WASD / šipky** pohybují hráčem, kamera ho sleduje a vpravo je minimapa.
- Vyjdi severním vchodem na **Meme louku**. Na sever pokračuje dalších sedm oblastí, od města přes džungli a led až k Nebeskému chrámu. Ploty, domy, stromy a krystaly jsou překážky.
- Přistup k divokému Brainrotovi a **podrž E 1,4 sekundy bez pohybu**. Chycení je zdarma. Neseš vždy jednoho Brainrota; odnes ho na pozemek na jihu. Teprve doma se přidá do sbírky a začne vydělávat.
- Divoký Brainrot se po chycení znovu objeví za 25 sekund hry na mapě.
- **E na pozemku** otevře správu impéria: vylepšení, úspěchy a prestige. **Esc** nebo **Zpět na mapu** menu zavře. Mimo pozemek není správa přístupná.
- **E u zamčené brány** odemkne další oblast za Coins. Lokace lze odemknout také ve správě. Šipky v horní části menu přepínají odemčené lokace, nikoli polohu hráče.
- **Obchod je odstraněný. Brainroty získáš pouze chycením na mapě.** Ve vylepšeních vyber šipkami konkrétní kus (`Kus 1 / 3`) a vylepši ho. Každý kus má vlastní level, cenu vylepšení a produkci; nový úlovek vždy začíná na levelu 1. Maximální level je 100, limit je 500 kusů od každého druhu.
- Všichni vlastnění Brainroti vydělávají i během výprav. Produkce jednoho kusu je základní produkce × jeho level × prestige násobitel.
- Prestige je dostupné po výdělku milionu Coins v aktuální éře. Resetuje postavičky, Coins, levely, lokace a nesený úlovek a vrátí hráče domů. Každý získaný prestige bod přidává trvalých +25 % produkce. Achievementy zůstávají.

## Oblasti a Brainroti

| Oblast | Cena brány | Postavičky |
| --- | ---: | --- |
| Meme louka | Zdarma | Tung Tung Tung Sahur, Tralalero Tralala |
| Brainrot city | 3 500 | Brr Brr Patapim, Ballerina Cappuccina |
| Kosmické impérium | 65 000 | Bombardiro Crocodilo, La Vacca Saturno |
| Banánová džungle | 650 000 | Chimpanzini Bananini, Bananita Dolphinita |
| Ledové království | 3 500 000 | Frigo Camelo, Penguino Cocosino |
| Lávové údolí | 18 000 000 | Dragon Cannelloni, Cactus Hipopotamo |
| Neonová dimenze | 95 000 000 | Neon Capybara, Disco Axolotlo |
| Nebeský chrám | 500 000 000 | Il Re del Brainrot, Serafino Galattico |

Oblasti mají vlastní palety, stavby a vegetaci, vodu nebo lávu, dlážděné cesty a dekorace. Postavičky používají vyhlazené sprity. Na pozemku se zobrazují na samostatných podstavcích.

## Ukládání a testy

**Ctrl+S** uloží postup; hra také ukládá každých 15 sekund a při zavření okna. Na Windows je save v `%LOCALAPPDATA%\BrainrotBorough\save.json`, jinde v `~/.local/share/BrainrotBorough/save.json`. Offline výdělek je omezený na 8 hodin. Vlastní soubor lze zadat pomocí `--save moje-hra.json`.

Po spuštění se objevíš na vlastním pozemku. Nesený úlovek se ukládá také a po návratu se automaticky odevzdá. Starší uložené hry se automaticky převedou: zachovají se Coins, lokace, počet Brainrotů i jejich dosavadní levely. Pokud měl druh společný level 3, každý jeho vlastněný kus dostane level 3 a dál se vylepšuje samostatně. Nečitelný save se nepřepisuje; hra zobrazí upozornění a vypne ukládání. Pro nový začátek přesuň save při vypnuté hře. Používej jednu instanci hry na jeden save.

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py --smoke-test --screenshot preview.png
```

Smoke test vykreslí pět snímků a skončí bez uložení. Pro běh bez obrazovky nastav `SDL_VIDEODRIVER=dummy` a `SDL_AUDIODRIVER=dummy`.

`main.py` obsahuje rozhraní a kreslení, `world.py` mapu a chytání, `game_state.py` ekonomiku a ukládání. Online leaderboard zatím není implementovaný.
