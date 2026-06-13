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

    def addFish(self, fishTypeName, amount):
        self.fishByType[fishTypeName] = self.fishByType.get(fishTypeName, 0) + amount
        self.fishCount += amount

    def clearFish(self):
        self.fishByType = {}
        self.fishCount = 0
