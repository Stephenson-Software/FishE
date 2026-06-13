# FishE

[![Run Unit Tests](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml/badge.svg)](https://github.com/Stephenson-Software/FishE/actions/workflows/test.yml)

This game allows you to explore a fishing village and perform actions in it.

## Features

### Multiple Save Files
FishE supports multiple save files, allowing you to maintain different game progressions simultaneously. When you start the game, you'll see a save file manager that displays:

- **Existing Saves**: View all your saved games with their progress (Day, Money, Fish count, Last Modified)
- **Create New Save**: Start a fresh game in a new save slot
- **Delete Save**: Remove unwanted save files
- **Quick Load**: Load any existing save file to continue your adventure

Each save file is stored in its own slot (slot_1, slot_2, etc.) in the `data/` directory, ensuring your saves never conflict with each other.

## Contributing

This project uses a simple, trunk-based branching model:

- `main` is the single long-lived branch and the source of truth.
- Branch off `main` for any change (e.g. `feature/...`, `fix/...`, `chore/...`).
- Open a pull request back into `main`. CI runs the test suite on every PR.
- Once CI is green and the change is reviewed, merge into `main` and delete the feature branch.

There is no `develop` branch — work flows directly off of and back into `main`.
