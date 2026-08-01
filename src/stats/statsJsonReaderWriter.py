import json
from stats.stats import Stats
from validation.schemaValidator import validate_against_schema

STATS_SCHEMA_PATH = "schemas/stats.json"


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
            "unlockedFeatures": stats.unlockedFeatures,
            "totalWorkersHired": stats.totalWorkersHired,
            "totalFishCaughtByCrew": stats.totalFishCaughtByCrew,
            "totalWagesPaid": stats.totalWagesPaid,
            "daysInBusiness": stats.daysInBusiness,
            "totalFishExported": stats.totalFishExported,
            "totalMoneyFromExports": stats.totalMoneyFromExports,
            "totalShippingPaid": stats.totalShippingPaid,
            "totalHaulingContracts": stats.totalHaulingContracts,
            "totalTransportRuns": stats.totalTransportRuns,
            "totalRaids": stats.totalRaids,
            "totalPlunder": stats.totalPlunder,
            "totalMoneyFromVoyages": stats.totalMoneyFromVoyages,
            "crewLostToPiracy": stats.crewLostToPiracy,
            "boatsOwned": stats.boatsOwned,
            "totalVoyagesCaptained": stats.totalVoyagesCaptained,
            "totalVoyagesFoundered": stats.totalVoyagesFoundered,
            "totalRentalIncome": stats.totalRentalIncome,
            "highestHomeTier": stats.highestHomeTier,
            "totalPropertiesBought": stats.totalPropertiesBought,
            "totalRentPaid": stats.totalRentPaid,
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
        stats.unlockedFeatures = statsJson.get(
            "unlockedFeatures", stats.unlockedFeatures
        )
        stats.totalWorkersHired = statsJson.get(
            "totalWorkersHired", stats.totalWorkersHired
        )
        stats.totalFishCaughtByCrew = statsJson.get(
            "totalFishCaughtByCrew", stats.totalFishCaughtByCrew
        )
        stats.totalWagesPaid = statsJson.get("totalWagesPaid", stats.totalWagesPaid)
        stats.daysInBusiness = statsJson.get("daysInBusiness", stats.daysInBusiness)
        stats.totalFishExported = statsJson.get(
            "totalFishExported", stats.totalFishExported
        )
        stats.totalMoneyFromExports = statsJson.get(
            "totalMoneyFromExports", stats.totalMoneyFromExports
        )
        stats.totalShippingPaid = statsJson.get(
            "totalShippingPaid", stats.totalShippingPaid
        )
        stats.totalHaulingContracts = statsJson.get(
            "totalHaulingContracts", stats.totalHaulingContracts
        )
        stats.totalTransportRuns = statsJson.get(
            "totalTransportRuns", stats.totalTransportRuns
        )
        stats.totalRaids = statsJson.get("totalRaids", stats.totalRaids)
        stats.totalPlunder = statsJson.get("totalPlunder", stats.totalPlunder)
        stats.totalMoneyFromVoyages = statsJson.get(
            "totalMoneyFromVoyages", stats.totalMoneyFromVoyages
        )
        stats.crewLostToPiracy = statsJson.get(
            "crewLostToPiracy", stats.crewLostToPiracy
        )
        stats.boatsOwned = statsJson.get("boatsOwned", stats.boatsOwned)
        stats.totalVoyagesCaptained = statsJson.get(
            "totalVoyagesCaptained", stats.totalVoyagesCaptained
        )
        stats.totalVoyagesFoundered = statsJson.get(
            "totalVoyagesFoundered", stats.totalVoyagesFoundered
        )
        stats.totalRentalIncome = statsJson.get(
            "totalRentalIncome", stats.totalRentalIncome
        )
        stats.highestHomeTier = statsJson.get("highestHomeTier", stats.highestHomeTier)
        stats.totalPropertiesBought = statsJson.get(
            "totalPropertiesBought", stats.totalPropertiesBought
        )
        stats.totalRentPaid = statsJson.get("totalRentPaid", stats.totalRentPaid)

        # Validate the resulting values (not the raw input) against the
        # schema - see PlayerJsonReaderWriter.createPlayerFromJson for why.
        validate_against_schema(self.createJsonFromStats(stats), STATS_SCHEMA_PATH)
        return stats

    def readStatsFromFile(self, statsJsonFile):
        statsJson = json.load(statsJsonFile)
        return self.createStatsFromJson(statsJson)

    def writeStatsToFile(self, stats, statsJsonFile):
        statsJson = self.createJsonFromStats(stats)
        json.dump(statsJson, statsJsonFile)
