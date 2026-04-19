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
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as f:
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
