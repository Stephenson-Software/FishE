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
        "moneyLostWhileDrunk": 5,
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
    assert statsFromJson.moneyLostWhileDrunk == 5


def test_createStatsFromJson_backward_compatibility():
    # Test that old save files without moneyLostWhileDrunk still work
    statsJsonReaderWriter = createStatsJsonReaderWriter()
    statsJson = {
        "totalFishCaught": 2,
        "totalMoneyMade": 2,
        "hoursSpentFishing": 2,
        "moneyMadeFromInterest": 2,
        "timesGottenDrunk": 2,
        "moneyLostFromGambling": 2,
    }

    statsFromJson = statsJsonReaderWriter.createStatsFromJson(statsJson)
    assert statsFromJson != None
    assert statsFromJson.totalFishCaught == 2
    assert statsFromJson.totalMoneyMade == 2
    assert statsFromJson.hoursSpentFishing == 2
    assert statsFromJson.moneyMadeFromInterest == 2
    assert statsFromJson.timesGottenDrunk == 2
    assert statsFromJson.moneyLostFromGambling == 2
    assert statsFromJson.moneyLostWhileDrunk == 0  # Should default to 0
