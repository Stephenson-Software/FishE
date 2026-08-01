# FishE

[![Run Unit Tests](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml/badge.svg)](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml)

This game allows you to explore a fishing village and perform actions in it.

## Features

### Play in your browser
FishE runs behind a single user-interface contract, so it supports multiple front-ends: the default text/console interface, a pygame window, and two browser-based ones. The entire game — save-file manager, fishing, shop, bank, tavern, and NPC dialogue — plays in the browser either way, and both render from the same client (`web/client.js`), so they look and behave identically. Adding a new front-end means implementing `BaseUserInterface` and adding a `UIType` + factory branch.

**In your own browser (`UIType.PYODIDE`)** — the game itself runs in your tab, under [Pyodide](https://pyodide.org). Nothing is sent to a server, every tab is its own game, and your **save files live in your browser's IndexedDB**, so they survive a reload and stay on your machine. This is how the game is deployed:

```bash
python3 web/build_zip.py    # bundle the game for the browser (once, and after any src/ change)
python3 web/serve.py
# then open http://127.0.0.1:8080
```

`web/serve.py` only serves files — it never runs the game. It does have to send the `Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` headers it sets, though: without them the page is not cross-origin isolated, `SharedArrayBuffer` is unavailable, and the browser cannot deliver your input to the game. Any proxy placed in front of it must preserve those headers.

**On a server (`UIType.WEB`)** — the game runs in the Python process and the browser is a terminal for it, with save files on the server's disk under `data/`. Handy for playing over a terminal-less machine on your own network, but everyone who opens the page shares one game and one set of saves:

```bash
python3 examples/web_app.py
# then open http://127.0.0.1:8000
```

Both use only the Python standard library; the Pyodide front-end loads its one runtime dependency (`jsonschema`) in the browser.

### One Thing at a Time
A new game opens on the docks with a rod, a bucket, and exactly one thing to do: **fish**. Everything else in the village arrives later, one option at a time, as you earn it — and each arrival tells you why it's there:

```
 You caught 7 Minnow over 6 hours! A perfect hook!  [Milestone unlocked: First Catch!]
 [Your basket is heavy with fish. Gilbert buys them at the shop - better go sell them.]

 [1] Fish
 [2] Go to Shop
 [3] Quit
```

Sell that basket and you're shown where you sleep; put in a few days and the villagers start talking to you; save up and the bank, the boats and the property market open up in turn. New entries are appended to the bottom of the menu, so an option you already know keeps its number. Only ever one new thing per screen, even when you earned two at once — so there's never a wall of choices to read.

Nothing is made harder by this; it's pacing, not difficulty. A save file from a player who already owns half the village opens with all of it available, exactly as before.

### Your Goal
Build a fortune of **$10,000** in total wealth (cash on hand plus savings in the bank). You're told about it once you've got your first $1,000 to your name, after which your progress toward the goal is shown in the status header. Reaching it earns a one-time victory — after which you're free to keep fishing or retire from the Home menu.

### Your Fleet
Once you can afford it, buy a **boat** at the docks ("Manage Fleet") — and then another, and another. Every boat is dedicated to one of four **roles**, and you can re-dedicate her whenever you like:

| Role | What she does |
|---|---|
| **Fishing** | Lands a catch every morning. The only role that brings in fish. |
| **Hauling** | Works the coastal freight trade daily, and her cargo hold raises how many fish an export run can carry. |
| **Piracy** | Takes coin and cargo off other vessels daily. Pays best, but a bad day damages the boat and now and then somebody doesn't come back. |
| **Transport** | Passenger runs: less money than freight, paid every day without fail and no risk to the boat. |

**Crew come from one shared roster.** You hire villagers by name (see below), and assign them to whichever boat you like — a new hire goes aboard the first boat with a free berth, and you can move anyone between boats from **Assign Crew to a Boat**. A second boat therefore means splitting the crew you have or hiring more, and since **wages are owed on every hand you've hired whether or not you found them a berth**, an idle boat is a real cost. If you can't make payroll, the hands you can't pay quit — the idle ones first.

Boats can be renamed, upgraded through the same Rowboat → Trawler → Fishing Fleet ladder (each hull individually), repaired, and sold back for a portion of their cost. Selling a boat doesn't fire her crew: they come ashore and stay on the payroll until you give them another berth or let them go.

### The Fleet Runs Itself
Every boat earns on its own each morning, according to her role — fishing boats land a catch, hauling and transport bring in money, and a piracy crew brings in the most of all. Wages come out automatically. You get an **overnight report** when a day passes telling you what the fleet did: what it landed, what it took, and — because a pirate crew doesn't always come home whole — who you lost.

That's the background. Here's the foreground:

### Taking the Helm
Choose **Take the Helm** at the docks to sail one of your own boats yourself. She earns nothing at home while you have her, and what you bring back is the point.

Before you go: pick **how far out** — a short run, the middle grounds, or the far water, each longer, richer and less forgiving than the last — and **provision her**. Stores are eaten every day by every hand aboard. Full stores covers exactly the days you planned and nothing else, so deep stores is real insurance and half rations is a real gamble.

Then you sail her a leg at a time. Each leg is a day at sea and puts a situation in front of you:

```
LEG 3 of 7   Hull 74%   Supplies 12   Crew 4   Hold $980

A squall builds to the north and the light goes the colour of a bruise.

 [1] Run before it
 [2] Hug the coast and lose a day
 [3] Iris Dunmore reads the sky for a gap
 [4] Ride it out at anchor
 [5] Break off and run for home (keep the hold)
```

**Who you brought decides what you can do.** That third option only exists because Iris Dunmore is aboard and reads the weather. Cormac Ide can find the seam in a leaking hull; Junia Marsh will go over the side after whatever sank; Bastian Roe can nurse a sick crew through the night; Sena Vale can work out where a merchantman will anchor so you take her asleep. Crewing a boat stops being a headcount and becomes casting.

Three things can only get worse unless you spend a decision on them — **hull**, **supplies** and **crew** — and the hold is only yours if you get home. You can **break off and run for home** at any point and keep everything you've taken, which is how you cut your losses when the hull is getting thin. If you press on and the hull gives out or the crew starve, the voyage is cut short instead: you lose everything aboard and limp back needing an expensive repair, but the boat is still yours and the game goes on.

The screens try to do the arithmetic for you rather than making you do it: each boat's line says what she earns a day, the fleet header says whether it clears its own payroll, the plan menu quotes what a voyage is worth in money rather than a multiplier, the provisioning menu says which day each option runs out on, and the docks screen tells you when a boat is sitting idle or too damaged to sail.

### Exporting to Other Villages
Gilbert's shop only has so much money each day, so once your crew is landing more fish than the village can absorb, the surplus just piles up. A **Trawler or better** can carry a hold out to neighbouring villages (and a boat dedicated to **hauling** carries half again as much), which have no daily limit at all — choose **Export Fish to Other Villages** at the docks. Three markets are reachable: **Saltmarsh** down the coast (cheap freight, modest prices), **Kestrel Cove** (a real harbour town that pays well for a proper haul), and **Thornhaven**, the far city market, which only a **Fishing Fleet** can reach and which pays double the village rate.

Each market charges more freight for a better price, so which one is worth sailing to depends on how much is in the hold — the menu shows what your current load would fetch at each before you commit. Your boat's hold sets how many fish go per run (a Trawler carries 250, a Fishing Fleet 600), the best fish are loaded first, and anything that doesn't fit waits for the next run. Freight is charged before you sail, so a run can never put you in debt, and the round trip costs you a day — your crew fish, wages come due, and rent falls while you're away.

### Home Ownership
You start **Homeless** — no home, and a low energy cap to show for it. From the Home menu, choose **Manage Home** to work your way up a housing ladder: Homeless → Rented Room → Driftwood Shack → Cozy Cottage → Sturdy Cabin → Waterfront Manor. Renting a room costs a daily fee (charged automatically each morning — miss a payment and you're evicted back to homeless) but builds no equity, so it's a bridge, not a destination. Buying a home costs money up front but is a real asset: moving to a different owned tier trades your current place in for the target one, so the price is the difference between what you get back for your old home and what the new one costs — moving up costs money, moving down (even back to renting) puts cash back in your pocket. Every rung raises the energy cap you refill to when you sleep, letting you fish longer between rests.

### Investment Properties
Separately from where you live, you can build a real-estate portfolio. At the bank, choose **Manage Investment Properties** to buy rental units around the village — Dockside Cottage, Fisherman's Rowhouse, Harborview Flat — that you don't live in yourself. Every unit you own pays out its own daily rental income automatically each new day, alongside bank interest and any crew wages, and any unit can be sold back for a portion of its price.

### Fishing
Cast a line at the docks to spend a random 1-10 hours fishing (10 energy per hour, so you need at least 10 energy to start). When a fish bites, react as fast as you can to set the hook — the faster you react, the better the catch quality, and a better rod (bought at the shop) gives you more time to react. What you reel in also depends on the day: fish feed best at dawn and dusk and go quiet under the midday sun, and the weather — rolled fresh each morning and shown in the docks description — can help (rain) or hurt (storms) your haul on top of that. Which species you land is random and weighted by rarity, from common Minnows to rare, high-value Golden Koi.

### Milestones
Lifetime stats — fish caught, money earned, hours spent fishing, crew hired, fish exported, raids run, voyages captained, homes owned, and more — unlock milestones as you reach their thresholds, from your very first catch up to owning the finest home in the village. Each milestone is announced once, the first time you reach it, even across save reloads.

### Selling Fish
Sell your catch at the shop. The shop has a limited amount of money each day that refills overnight, so a very large haul may sell out the shop and need to be finished the next day — sell regularly, and park your earnings in the bank or reinvest them in gear and your crew. Once you outgrow the shop entirely, a big enough boat lets you ship the surplus out to other villages instead (see Exporting to Other Villages above).

### Multiple Save Files
FishE supports multiple save files, allowing you to maintain different game progressions simultaneously. When you start the game, you'll see a save file manager that displays:

- **Existing Saves**: each save slot is listed with a snapshot of its progress (Day, Money, and Fish count)
- **Create New Save**: Start a fresh game in a new save slot
- **Delete Save**: Remove unwanted save files
- **Load**: Pick any existing save slot to continue your adventure

Each save file is stored in its own slot (slot_1, slot_2, etc.) in the `data/` directory, ensuring your saves never conflict with each other. Set `FISHE_SAVE_DIR` to keep them somewhere else.

When you play in your own browser (the Pyodide front-end above), those same slots are written to your browser's IndexedDB instead of to disk — creating, saving and deleting a slot all take effect there, so your progress is waiting for you when you come back to the tab. They belong to that browser on that machine: clearing the site's data clears them, and they don't follow you to another browser or another device.

## Contributing

This project uses a simple, trunk-based branching model:

- `main` is the single long-lived branch and the source of truth.
- Branch off `main` for any change (e.g. `feature/...`, `fix/...`, `chore/...`).
- Open a pull request back into `main`. CI runs the test suite on every PR.
- Once CI is green and the change is reviewed, merge into `main` and delete the feature branch.

There is no `develop` branch — work flows directly off of and back into `main`.
