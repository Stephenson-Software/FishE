import json
from stats.stats import Stats


class StatsJsonReaderWriter:
    def createJsonFromStats(self, stats: Stats):
        return {
            "totalFishCaught": stats.totalFishCaught,
            "totalMoneyMade": stats.totalMoneyMade,
            "hoursSpentFishing": stats.hoursSpentFishing,
            "moneyMadeFromInterest": stats.moneyMadeFromInterest,
            "timesGottenDrunk": stats.timesGottenDrunk,
            "moneyLostFromGambling": stats.moneyLostFromGambling,
            "moneyLostWhileDrunk": stats.moneyLostWhileDrunk,
        }

    def createStatsFromJson(self, statsJson):
        stats = Stats()
        stats.totalFishCaught = statsJson["totalFishCaught"]
        stats.totalMoneyMade = statsJson["totalMoneyMade"]
        stats.hoursSpentFishing = statsJson["hoursSpentFishing"]
        stats.moneyMadeFromInterest = statsJson["moneyMadeFromInterest"]
        stats.timesGottenDrunk = statsJson["timesGottenDrunk"]
        stats.moneyLostFromGambling = statsJson["moneyLostFromGambling"]
        # Handle backward compatibility for existing save files
        stats.moneyLostWhileDrunk = statsJson.get("moneyLostWhileDrunk", 0)
        return stats

    def readStatsFromFile(self, statsJsonFile):
        statsJson = json.load(statsJsonFile)
        return self.createStatsFromJson(statsJson)

    def writeStatsToFile(self, stats, statsJsonFile):
        statsJson = self.createJsonFromStats(stats)
        json.dump(statsJson, statsJsonFile)
