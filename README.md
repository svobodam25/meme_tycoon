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
- **E na pozemku** otevře správu impéria: inventář, úspěchy a prestige. **Esc** nebo **Zpět na mapu** menu zavře. Mimo pozemek není správa přístupná.
- **E u zamčené brány** odemkne další oblast za Coins. Lokace lze odemknout také v panelu správy u úspěchů a prestige. Inventář vždy ukazuje úlovky ze všech lokací.
- **Brainroty získáš pouze chycením na mapě.** Každý úlovek má vlastní obsazený slot v inventáři; prázdné sloty se nekreslí. Dva stejní Brainroti zabírají dva samostatné sloty. Základní pozemek má **8 slotů**; obsazení i kapacitu vidíš v inventáři a na mapě.
- Klikni na slot: vpravo se zobrazí větší postavička, její rarita, původ, číslo kusu, level, produkce a tlačítko vylepšení. Vylepšení platí jen pro vybraný kus. Nový úlovek začíná na levelu 1, maximální level je 100.
- Inventář posouváš **kolečkem myši**, **Page Up / Page Down** nebo **Home / End**. **Šipky** vybírají sousední sloty a posunou seznam k výběru. Zobrazují se jen sloty ve viditelné části seznamu, takže není nutné vykreslovat celou velkou sbírku najednou.
- Vybraného Brainrota můžeš **prodat** tlačítkem pod vylepšením. Prodej vyžaduje potvrzení; odstraní právě tento kus včetně jeho levelů, uvolní slot a vyplatí polovinu jeho základní hodnoty × aktuální level (zaokrouhleno nahoru). Ostatní kusy zůstanou beze změny. Prodej se nepočítá jako produkční výdělek pro prestige.
- Když je pozemek plný, dalšího Brainrota nechytíš. Nesený úlovek si rezervuje jeden slot, takže při návratu domů má vždy místo. Pro další lov nejdřív někoho prodej nebo rozšiř pozemek.
- Tlačítkem **Pozemek +8 slotů** nahoře v inventáři koupíš rozšíření. Přidá 8 slotů, rozšíří oplocení a prodlouží pozemek na mapě o dvě další řady podstavců. Celkem lze koupit šest rozšíření: za **1 000**, **4 000**, **16 000**, **64 000**, **256 000** a **1 024 000 Coins**. Nová hra tak může vyrůst z 8 na **56 slotů**. Rozšíření pozemku zůstávají i po prestige.
- **Každý vlastněný Brainrot stojí na mapě samostatně**, včetně stejných druhů. Pod každým vidíš číslo kusu a jeho aktuální level, například `#2 · Lv 7`. Číslo odpovídá kusu daného druhu v inventáři. Po vylepšení se štítek aktualizuje a po prodeji zůstávající kusy zaplní volné místo.
- Pozemkem vede volná středová cesta. Kamera tě sleduje i v dalších řadách na jihu, takže celý velký pozemek projdeš pomocí WASD / šipek. Dům a spodní plot se při rozšíření posunou za poslední řadu; postavičky se neskládají na sebe ani do jedné ikony s počtem.
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

Oblasti mají vlastní palety, stavby a vegetaci, vodu nebo lávu, dlážděné cesty a dekorace. Všech 16 druhů používá vlastní vyhlazenou kresbu: Sahur má dřevěné letokruhy a pálku, Tralalero tři tenisky, Bombardiro křídla a vrtuli, Frigo Camelo ledničkové tělo a velbloudí hlavu. Na pozemku má každý jednotlivý kus vlastní podstavec a štítek s levelem.

## Ukládání a testy

**Ctrl+S** uloží postup; hra také ukládá každých 15 sekund a při zavření okna. Na Windows je save v `%LOCALAPPDATA%\BrainrotBorough\save.json`, jinde v `~/.local/share/BrainrotBorough/save.json`. Offline výdělek je omezený na 8 hodin. Vlastní soubor lze zadat pomocí `--save moje-hra.json`.

Po spuštění se objevíš na vlastním pozemku. Nesený úlovek se ukládá také a po návratu se automaticky odevzdá. Starší uložené hry se automaticky převedou: zachovají se Coins, lokace, počet Brainrotů i jejich dosavadní levely. Pokud měl druh společný level 3, každý jeho vlastněný kus dostane level 3 a dál se vylepšuje samostatně. Sbírky z verze s neomezeným inventářem dostanou zdarma dostatečnou základní kapacitu, zaokrouhlenou na násobek osmi včetně neseného úlovku. Nic se nemaže; zakoupená rozšíření tuto kapacitu dále navyšují. Nečitelný save se nepřepisuje; hra zobrazí upozornění a vypne ukládání. Pro nový začátek přesuň save při vypnuté hře. Používej jednu instanci hry na jeden save.

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py --smoke-test --screenshot preview.png
```

Smoke test vykreslí pět snímků a skončí bez uložení. Pro běh bez obrazovky nastav `SDL_VIDEODRIVER=dummy` a `SDL_AUDIODRIVER=dummy`.

`main.py` obsahuje hlavní rozhraní, `inventory.py` inventář jednotlivých kusů, `sprites.py` kresby postaviček, `world.py` mapu a chytání a `game_state.py` ekonomiku a ukládání. Online leaderboard zatím není implementovaný.
