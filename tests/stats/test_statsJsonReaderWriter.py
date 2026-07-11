from src.stats.stats import Stats
from src.stats import statsJsonReaderWriter
import json
from jsonschema import validate


def createStatsJsonReaderWriter():
    return statsJsonReaderWriter.StatsJsonReaderWriter()


def createStats():
    return Stats()


def getStatsSchema():
    # load json from file
    with open("schemas/stats.json") as json_file:
        return json.load(json_file)


def test_initialization():
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    assert statsJsonReaderWriter != None


def test_createJsonFromStats():
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    stats = createStats()
    statsJson = statsJsonReaderWriter.createJsonFromStats(stats)
    assert statsJson != None

    # validate
    statsSchema = getStatsSchema()
    validate(statsJson, statsSchema)


def test_createStatsFromJson():
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {
        "totalFishCaught": 2,
        "totalMoneyMade": 2,
        "hoursSpentFishing": 2,
        "moneyMadeFromInterest": 2,
        "timesGottenDrunk": 2,
        "moneyLostFromGambling": 2,
        "moneyLostWhileDrunk": 2,
    }

    # validate
    statsSchema = getStatsSchema()
    validate(statsJson, statsSchema)

    statsFromJson = statsJsonReaderWriter.createStatsFromJson(statsJson)
    assert statsFromJson != None
    assert statsFromJson.totalFishCaught == 2
    assert statsFromJson.totalMoneyMade == 2
    assert statsFromJson.hoursSpentFishing == 2
    assert statsFromJson.moneyMadeFromInterest == 2
    assert statsFromJson.timesGottenDrunk == 2
    assert statsFromJson.moneyLostFromGambling == 2
    assert statsFromJson.moneyLostWhileDrunk == 2


def test_earnedMilestones_round_trips():
    # prepare
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    stats = createStats()
    stats.earnedMilestones = ["First Catch", "Big Earner"]

    # call - serialize then deserialize
    statsJson = statsJsonReaderWriter.createJsonFromStats(stats)
    restored = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check
    assert statsJson["earnedMilestones"] == ["First Catch", "Big Earner"]
    assert restored.earnedMilestones == ["First Catch", "Big Earner"]


def test_createStatsFromJson_missingEarnedMilestones_defaultsToEmpty():
    # prepare - an older save with no earnedMilestones field
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {
        "totalFishCaught": 1,
        "totalMoneyMade": 1,
        "hoursSpentFishing": 1,
        "moneyMadeFromInterest": 1,
        "timesGottenDrunk": 1,
        "moneyLostFromGambling": 1,
        "moneyLostWhileDrunk": 1,
    }

    # call
    stats = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check - backward compatible default
    assert stats.earnedMilestones == []


def test_businessStats_round_trip():
    # prepare
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    stats = createStats()
    stats.totalWorkersHired = 4
    stats.totalFishCaughtByCrew = 120
    stats.totalWagesPaid = 300
    stats.daysInBusiness = 15

    # call - serialize then deserialize
    statsJson = statsJsonReaderWriter.createJsonFromStats(stats)
    restored = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check
    assert statsJson["totalWorkersHired"] == 4
    assert statsJson["totalFishCaughtByCrew"] == 120
    assert statsJson["totalWagesPaid"] == 300
    assert statsJson["daysInBusiness"] == 15
    assert restored.totalWorkersHired == 4
    assert restored.totalFishCaughtByCrew == 120
    assert restored.totalWagesPaid == 300
    assert restored.daysInBusiness == 15


def test_createStatsFromJson_missingBusinessStats_defaultsToZero():
    # prepare - an older save with no business-stat fields
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {
        "totalFishCaught": 1,
        "totalMoneyMade": 1,
    }

    # call
    stats = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check - backward compatible defaults
    assert stats.totalWorkersHired == 0
    assert stats.totalFishCaughtByCrew == 0
    assert stats.totalWagesPaid == 0
    assert stats.daysInBusiness == 0


def test_housingStats_round_trip():
    # prepare
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    stats = createStats()
    stats.totalRentalIncome = 85
    stats.highestHomeTier = 3

    # call - serialize then deserialize
    statsJson = statsJsonReaderWriter.createJsonFromStats(stats)
    restored = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check
    assert statsJson["totalRentalIncome"] == 85
    assert statsJson["highestHomeTier"] == 3
    assert restored.totalRentalIncome == 85
    assert restored.highestHomeTier == 3

    # validate against the schema
    validate(statsJson, getStatsSchema())


def test_createStatsFromJson_missingHousingStats_defaults():
    # prepare - an older save with no housing-stat fields
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {
        "totalFishCaught": 1,
        "totalMoneyMade": 1,
    }

    # call
    stats = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check - backward compatible defaults
    assert stats.totalRentalIncome == 0
    assert stats.highestHomeTier == 1


def test_writeStatsToFile():
    # prepare
    import tempfile

    statsJsonReaderWriter = createStatsJsonReaderWriter()
    stats = createStats()
    stats.totalFishCaught = 50
    stats.totalMoneyMade = 1000

    # call
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
        statsJsonReaderWriter.writeStatsToFile(stats, f)
        temp_file_path = f.name

    # check - read back the file and verify
    with open(temp_file_path, "r") as f:
        statsJson = json.load(f)

    assert statsJson["totalFishCaught"] == 50
    assert statsJson["totalMoneyMade"] == 1000

    # cleanup
    import os

    os.remove(temp_file_path)


def test_readStatsFromFile():
    # prepare
    import tempfile

    statsJson = {
        "totalFishCaught": 75,
        "totalMoneyMade": 1500,
        "hoursSpentFishing": 20,
        "moneyMadeFromInterest": 100,
        "timesGottenDrunk": 5,
        "moneyLostFromGambling": 200,
    }

    # Write test data to temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(statsJson, f)
        temp_file_path = f.name

    # call
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    with open(temp_file_path, "r") as f:
        stats = statsJsonReaderWriter.readStatsFromFile(f)

    # check
    assert stats.totalFishCaught == 75
    assert stats.totalMoneyMade == 1500
    assert stats.hoursSpentFishing == 20
    assert stats.moneyMadeFromInterest == 100
    assert stats.timesGottenDrunk == 5
    assert stats.moneyLostFromGambling == 200

    # cleanup
    import os

    os.remove(temp_file_path)


def test_createStatsFromJson_missingAllFields_usesDefaults():
    # prepare - a corrupt/partial save with no recognizable fields
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {}

    # call - must not raise KeyError
    stats = statsJsonReaderWriter.createStatsFromJson(statsJson)

    # check - every field falls back to the Stats() default
    defaults = Stats()
    assert stats.totalFishCaught == defaults.totalFishCaught
    assert stats.totalMoneyMade == defaults.totalMoneyMade
    assert stats.hoursSpentFishing == defaults.hoursSpentFishing
    assert stats.moneyMadeFromInterest == defaults.moneyMadeFromInterest
    assert stats.timesGottenDrunk == defaults.timesGottenDrunk
    assert stats.moneyLostFromGambling == defaults.moneyLostFromGambling
    assert stats.moneyLostWhileDrunk == defaults.moneyLostWhileDrunk
