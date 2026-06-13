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
            "earnedMilestones": stats.earnedMilestones,
        }

    def createStatsFromJson(self, statsJson):
        # Read each field with a fallback to the freshly-constructed Stats'
        # default, so a save file missing any field loads gracefully instead of
        # raising KeyError (backwards compatibility for older/partial saves).
        stats = Stats()
        stats.totalFishCaught = statsJson.get("totalFishCaught", stats.totalFishCaught)
        stats.totalMoneyMade = statsJson.get("totalMoneyMade", stats.totalMoneyMade)
        stats.hoursSpentFishing = statsJson.get(
            "hoursSpentFishing", stats.hoursSpentFishing
        )
        stats.moneyMadeFromInterest = statsJson.get(
            "moneyMadeFromInterest", stats.moneyMadeFromInterest
        )
        stats.timesGottenDrunk = statsJson.get(
            "timesGottenDrunk", stats.timesGottenDrunk
        )
        stats.moneyLostFromGambling = statsJson.get(
            "moneyLostFromGambling", stats.moneyLostFromGambling
        )
        stats.moneyLostWhileDrunk = statsJson.get(
            "moneyLostWhileDrunk", stats.moneyLostWhileDrunk
        )
        stats.earnedMilestones = statsJson.get(
            "earnedMilestones", stats.earnedMilestones
        )
        return stats

    def readStatsFromFile(self, statsJsonFile):
        statsJson = json.load(statsJsonFile)
        return self.createStatsFromJson(statsJson)

    def writeStatsToFile(self, stats, statsJsonFile):
        statsJson = self.createJsonFromStats(stats)
        json.dump(statsJson, statsJsonFile)
