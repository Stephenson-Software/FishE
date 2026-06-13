# @author Daniel McCoy Stephenson
class Config:
    def __init__(self):
        # Save file paths
        self.dataDirectory = "data"
        self.playerSaveFile = "data/player.json"
        self.statsSaveFile = "data/stats.json"
        self.timeServiceSaveFile = "data/timeService.json"
        
        # Initial player values
        self.initialMoney = 20
        self.initialEnergy = 100
        self.initialFishCount = 0
        self.initialMoneyInBank = 0.01
        self.initialFishMultiplier = 1
        self.initialPriceForBait = 50
