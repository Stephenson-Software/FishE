# FishE

This game allows you to explore a fishing village and perform actions in it.

## UI Types

FishE now supports two different user interface types:

### Console UI (Default)
Traditional text-based interface that runs in the terminal.
```bash
python3 src/fishE.py
# or explicitly
python3 src/fishE.py --ui console
```

### Pygame UI
Windowed interface with graphics and visual styling.
```bash
python3 src/fishE.py --ui pygame
```

## Features

Both interfaces provide identical game functionality:
- Fish at the docks to catch fish and earn money
- Visit the shop to sell fish and buy better bait
- Go to the bank to deposit/withdraw money
- Relax at the tavern (get drunk or gamble)
- View your stats at home
- Save/load game progress automatically

## Requirements

- Python 3.x
- pygame (for windowed UI mode)

Install pygame: `pip install pygame`

## Development

Run tests: `./test.sh`
Run demo: `python3 demo_ui.py`
