import os


# @author Daniel McCoy Stephenson
class Config:
    def __init__(self):
        # Save file paths. FISHE_SAVE_DIR relocates the whole save directory,
        # which deployments use to point the game somewhere other than a
        # cwd-relative "data" — a mounted volume for a server install, or the
        # Worker-side directory that the Pyodide front-end mirrors to the
        # browser's IndexedDB (see browserSaveSync and web/game-worker.js).
        self.dataDirectory = os.environ.get("FISHE_SAVE_DIR") or "data"
        self.playerSaveFile = os.path.join(self.dataDirectory, "player.json")
        self.statsSaveFile = os.path.join(self.dataDirectory, "stats.json")
        self.timeServiceSaveFile = os.path.join(self.dataDirectory, "timeService.json")

        # Initial player values
        self.initialMoney = 20
        self.initialEnergy = 100
        self.initialFishCount = 0
        self.initialMoneyInBank = 0.01
        self.initialFishMultiplier = 1
        self.initialPriceForBait = 50
