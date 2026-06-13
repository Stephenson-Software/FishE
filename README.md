# FishE

[![Run Unit Tests](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml/badge.svg)](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml)

This game allows you to explore a fishing village and perform actions in it.

## Features

### Play in your browser (web interface)
FishE runs behind a single user-interface contract, so it supports multiple front-ends: the default text/console interface, a pygame window, and a browser-based **web interface**. To play in the browser, run the example web app and open the printed URL:

```bash
python3 examples/web_app.py
# then open http://127.0.0.1:8000
```

The entire game — save-file manager, fishing, shop, bank, tavern, and NPC dialogue — plays in the browser, with no extra dependencies (it uses only the Python standard library). Adding a new front-end means implementing `BaseUserInterface` and adding a `UIType` + factory branch.

### Your Goal
Build a fortune of **$10,000** in total wealth (cash on hand plus savings in the bank). Your progress toward the goal is shown in the status header, and reaching it earns a one-time victory — after which you're free to keep fishing or retire from the Home menu.

### Fishing Business
Once you can afford it, buy a **boat** at the docks ("Manage Boat & Crew") and **hire workers**. Each day your crew brings in a passive catch in exchange for a daily wage — turning saved-up money into ongoing production. If you over-hire and can't make payroll, the workers you can't pay quit, so keep enough cash on hand to cover wages.

### Selling Fish
Sell your catch at the shop. The shop has a limited amount of money each day that refills overnight, so a very large haul may sell out the shop and need to be finished the next day — sell regularly, and park your earnings in the bank or reinvest them in gear and your crew.

### Multiple Save Files
FishE supports multiple save files, allowing you to maintain different game progressions simultaneously. When you start the game, you'll see a save file manager that displays:

- **Existing Saves**: each save slot is listed with a snapshot of its progress (Day, Money, and Fish count)
- **Create New Save**: Start a fresh game in a new save slot
- **Delete Save**: Remove unwanted save files
- **Load**: Pick any existing save slot to continue your adventure

Each save file is stored in its own slot (slot_1, slot_2, etc.) in the `data/` directory, ensuring your saves never conflict with each other.

## Contributing

This project uses a simple, trunk-based branching model:

- `main` is the single long-lived branch and the source of truth.
- Branch off `main` for any change (e.g. `feature/...`, `fix/...`, `chore/...`).
- Open a pull request back into `main`. CI runs the test suite on every PR.
- Once CI is green and the change is reviewed, merge into `main` and delete the feature branch.

There is no `develop` branch — work flows directly off of and back into `main`.
