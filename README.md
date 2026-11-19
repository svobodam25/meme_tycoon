# Meme Tycoon

2D idle tycoon v Pythonu a Pygame. Prozkoumávej mapu, chytej Brainroty, nos je na vlastní pozemek a jejich výdělek investuj do jednotlivých postaviček a nových oblastí. Hra má 8 oblastí, 16 druhů Brainrotů, prestige, achievementy a automatické ukládání. Grafika je kreslená přímo v Pygame.

## Spuštění hry Meme Tycoon

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
- **Nové druhy objevíš chycením na mapě; další kusy můžeš koupit v obchodě.** Každý kus má vlastní obsazený slot v inventáři; prázdné sloty se nekreslí. Dva stejní Brainroti zabírají dva samostatné sloty. Základní pozemek má **8 slotů**; obsazení i kapacitu vidíš v inventáři a na mapě.
- Klikni na slot: vpravo se zobrazí větší postavička, její rarita, původ, číslo kusu, level, produkce a tlačítko vylepšení. Vylepšení platí jen pro vybraný kus. Nový úlovek začíná na levelu 1, maximální level je 100.
- Vylepšení mají klesající přínos: level 100 dává nejvýše 3× základní produkci a vždy méně než první druh následující vyšší rarity při stejném prestige. Násobitel levelu L je `1 + B × log₁₀₀(L)`, kde `B = min(2; 0,9 × produkce první vyšší rarity / základní produkce − 1)`; poslední rarita používá B = 2. Cena je `B × max(základní produkce × 90; základní hodnota × 0,12) × (1 + 0,25 × (L − 1))`, zaokrouhlená nahoru. První upgrade se bez prestige vrací z přidané produkce za přibližně 10 minut nebo déle, další pomaleji; prestige návratnost zkracuje. Sahur například stojí na level 2 **180 Coins** a produkce roste z 1 na přibližně **1,301 Coins/s**. Inventář ukazuje přírůstek i návratnost v minutách; jde o cenu dělenou přidaným výdělkem, nikoli o čas potřebný na našetření celou sbírkou.
- Inventář posouváš **kolečkem myši**, **Page Up / Page Down** nebo **Home / End**. **Šipky** vybírají sousední sloty a posunou seznam k výběru. Zobrazují se jen sloty ve viditelné části seznamu, takže není nutné vykreslovat celou velkou sbírku najednou.
- Vybraného Brainrota můžeš **prodat** tlačítkem pod vylepšením. Prodej vyžaduje potvrzení; odstraní právě tento kus včetně jeho levelů, uvolní slot a vyplatí polovinu jeho základní hodnoty × násobitel levelu (zaokrouhleno nahoru). Prodejní hodnota tak roste stejně pozvolna jako produkce a opakované vylepšování a prodávání nevytváří zisk. Ostatní kusy zůstanou beze změny. Prodej se nepočítá jako produkční výdělek pro prestige.
- Když je pozemek plný, dalšího Brainrota nechytíš. Nesený úlovek si rezervuje jeden slot, takže při návratu domů má vždy místo. Pro další lov nejdřív někoho prodej nebo rozšiř pozemek.
- Tlačítkem **Pozemek +8 slotů** nahoře v inventáři koupíš rozšíření. Přidá 8 slotů, rozšíří oplocení a prodlouží pozemek na mapě o dvě další řady podstavců. Celkem lze koupit šest rozšíření: za **1 000**, **4 000**, **16 000**, **64 000**, **256 000** a **1 024 000 Coins**. Nová hra tak může vyrůst z 8 na **56 slotů**. Rozšíření pozemku zůstávají i po prestige.
- **Každý vlastněný Brainrot stojí na mapě samostatně**, včetně stejných druhů. Pod každým vidíš číslo kusu a jeho aktuální level, například `#2 · Lv 7`. Číslo odpovídá kusu daného druhu v inventáři. Po vylepšení se štítek aktualizuje a po prodeji zůstávající kusy zaplní volné místo.
- Pozemkem vede volná středová cesta. Kamera tě sleduje i v dalších řadách na jihu, takže celý velký pozemek projdeš pomocí WASD / šipek. Dům a spodní plot se při rozšíření posunou za poslední řadu; postavičky se neskládají na sebe ani do jedné ikony s počtem.
- Všichni vlastnění Brainroti vydělávají i během výprav. Produkce jednoho kusu je základní produkce × násobitel levelu × prestige násobitel. Nové vyvážení platí i pro dosavadní postavy a offline výdělek; uložené levely se zachovávají.
- Výdělky se zpomalují hlavně ke konci: první dva druhy mají původní produkci 1 a 7 Coins/s, prostřední lokace rostou pozvolněji a poslední druhy vydělávají 18 000 a 24 000 Coins/s místo původních 1,1 a 1,9 milionu. Bez prestige tak postup do posledních lokací výrazně zpomalí. Stejné hodnoty platí i pro offline výdělek.
- V záložce **Obchod** můžeš koupit další kus druhu, který jsi už chytil a donesl domů. Cena je **4× základní hodnota** (např. Sahur 100 Coins), takže chytání zdarma se vyplatí víc. Nákup vyžaduje volný slot a odemčenou původní lokaci; nový kus začíná na levelu 1. Objevené druhy zůstávají odemčené i po prodeji a prestige. U starších savů se objeví všechny aktuálně vlastněné druhy.
- První prestige **stojí milion aktuálně našetřených Coins**. Celkový výdělek éry nestačí: utracené peníze se do ceny nepočítají. Každé provedení přidá jeden prestige a **zdvojnásobí produkci** (2×, 4×, 8×…). Cena dalšího prestige roste **4×**: 1, 4, 16, 64 milionů Coins atd. Cena je součástí resetu všech Coins na počátečních 100; případný přebytek se nepřenáší. Resetuje také postavičky, levely, lokace a nesený úlovek a vrátí hráče domů. Achievementy, objevené druhy a pozemek zůstávají. Výdělek éry se nadále zaznamenává pro místní žebříček.

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

Vyšší rarity mají výraznější palety: LEGENDARY zlatou, MYTHICAL fialovou a růžovou, CELESTIAL azurovou a modrou, DIVINE ohnivou, SECRET neonově zelenou a TRANSCENDENT zářivou zlatou a krémovou. Barvy se zobrazují na postavách i v inventáři.

Záložka **Úspěchy** obsahuje 18 achievementů na třech stránkách. Nové cíle zahrnují rozšiřování pozemku, levely 10 a 100, vzácné úlovky, objevení všech druhů, poslední lokaci, produkci 100 000 Coins/s, miliardu celkového výdělku a opakované prestige. Splněné achievementy zůstávají po prestige.

Záložka **Žebříčky** nabízí tři místní TOP 5: výdělek éry, produkci při prestige a počet vlastněných kusů při prestige. Aktuální éra se porovnává živě; dokončená se zapíše před resetem. Produkce a sbírka jsou stav při prestige, nikoli historická maxima během éry. Rekordy se uchovávají v savu i po prestige. Žebříčky porovnávají tvoje vlastní éry, nejsou online ani multiplayerové; starší savy začnou zaznamenávat dokončené éry od této aktualizace.

**Proč místní žebříček místo online?** Pro rozsah této jednoduché hry by byl důvěryhodný online leaderboard příliš složitý na vytvoření a následnou údržbu. Vyžadoval by server, databázi, identifikaci hráčů, bezpečné odesílání výsledků, řešení výpadků připojení a průběžný provoz hostingu. Samotné nahrání čísel by navíc nestačilo: místní save lze upravit, takže by bylo nutné ověřovat výsledky a bránit podvádění, aby soutěž mezi hráči dávala smysl.

Místní žebříček odpovídá hře pro jednoho hráče: funguje bez internetu, účtu i serveru a umožňuje sledovat vlastní zlepšování mezi prestige érami. Nabízí tak motivaci překonávat osobní rekordy bez složitosti online služby. Není určený k ověřenému porovnávání různých hráčů; online varianta může být samostatným budoucím rozšířením.

**Ctrl+S** uloží postup; hra také ukládá každých 15 sekund a při zavření okna. Na Windows je save v `%LOCALAPPDATA%\MemeTycoon\save.json`, jinde v `~/.local/share/MemeTycoon/save.json`. Offline výdělek je omezený na 8 hodin. Vlastní soubor lze zadat pomocí `--save moje-hra.json`.

Pokud nový výchozí save neexistuje, hra načte dosavadní `BrainrotBorough/save.json` ze stejného nadřazeného adresáře. Další ukládání používá složku `MemeTycoon`; původní soubor zůstane zachovaný. Vlastní cesta přes `--save` se nemění.

Po spuštění se objevíš na vlastním pozemku. Nesený úlovek se ukládá také a po návratu se automaticky odevzdá. Starší uložené hry se automaticky převedou: zachovají se Coins, lokace, počet Brainrotů i jejich dosavadní levely. Pokud měl druh společný level 3, každý jeho vlastněný kus dostane level 3 a dál se vylepšuje samostatně. Sbírky z verze s neomezeným inventářem dostanou zdarma dostatečnou základní kapacitu, zaokrouhlenou na násobek osmi včetně neseného úlovku. Nic se nemaže; zakoupená rozšíření tuto kapacitu dále navyšují. Nečitelný save se nepřepisuje; hra zobrazí upozornění a vypne ukládání. Pro nový začátek přesuň save při vypnuté hře. Používej jednu instanci hry na jeden save.

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe main.py --smoke-test --screenshot preview.png
```

Smoke test vykreslí pět snímků a skončí bez uložení. Pro běh bez obrazovky nastav `SDL_VIDEODRIVER=dummy` a `SDL_AUDIODRIVER=dummy`.

`main.py` obsahuje hlavní rozhraní, `inventory.py` inventář jednotlivých kusů, `sprites.py` kresby postaviček, `world.py` mapu a chytání a `game_state.py` ekonomiku a ukládání. Online leaderboard zatím není implementovaný.
