import os


# @author Daniel McCoy Stephenson
class Player:
    def __init__(self):
        self.fishCount = 0
        self.money = 20
        self.moneyInBank = 0.01
        self.fishMultiplier = 1
        self.priceForBait = 50
        self.energy = 100
        self.rodLevel = 1
        # Per-species breakdown of the fish currently held. fishCount remains the
        # aggregate total; addFish/clearFish keep the two in sync.
        self.fishByType = {}
        # Fishing business: a boat unlocks hiring workers who bring in a passive
        # daily catch for a daily wage (see src/business).
        self.hasBoat = False
        self.workers = 0
        # Testing/debug cheat: when on, every money check passes and spendMoney
        # becomes a no-op, so cash never actually runs out. Not persisted to save
        # files - it's a runtime toggle, not game progress. Defaults from the
        # FISHE_OPERATOR_MODE env var so it can be turned on for a whole session
        # (e.g. `FISHE_OPERATOR_MODE=1 python3 src/fishE.py`) without code changes.
        self.operatorMode = os.environ.get("FISHE_OPERATOR_MODE", "").lower() in (
            "1",
            "true",
            "yes",
        )

    def canAfford(self, cost):
        return self.operatorMode or self.money >= cost

    def spendMoney(self, cost):
        if not self.operatorMode:
            self.money -= cost

    def hasEnergy(self, amount):
        return self.operatorMode or self.energy >= amount

    def spendEnergy(self, amount):
        if not self.operatorMode:
            self.energy -= amount

    def addFish(self, fishTypeName, amount):
        self.fishByType[fishTypeName] = self.fishByType.get(fishTypeName, 0) + amount
        self.fishCount += amount

    def clearFish(self):
        self.fishByType = {}
        self.fishCount = 0
