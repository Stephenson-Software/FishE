from src.player.player import Player
from src.stats.stats import Stats
from src.world import timeServiceJsonReaderWriter
from src.world.timeService import TimeService
import json
import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def createTimeServiceJsonReaderWriter():
    return timeServiceJsonReaderWriter.TimeServiceJsonReaderWriter()


def createTimeService():
    player = Player()
    stats = Stats()
    return TimeService(player, stats)


def getTimeServiceSchema():
    # load json from file
    with open("schemas/timeService.json") as json_file:
        return json.load(json_file)


def test_initialization():
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    assert timeServiceJsonReaderWriter != None


def test_createJsonFromTimeService():
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    timeService = createTimeService()
    timeServiceJson = timeServiceJsonReaderWriter.createJsonFromTimeService(timeService)
    assert timeServiceJson != None

    # validate
    timeServiceSchema = getTimeServiceSchema()
    validate(timeServiceJson, timeServiceSchema)


def test_createTimeServiceFromJson():
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    timeServiceJson = {"time": 8, "day": 1, "weather": "rainy"}

    # validate
    timeServiceSchema = getTimeServiceSchema()
    validate(timeServiceJson, timeServiceSchema)

    player = Player()
    stats = Stats()
    timeServiceFromJson = timeServiceJsonReaderWriter.createTimeServiceFromJson(
        timeServiceJson, player, stats
    )
    assert timeServiceFromJson != None
    assert timeServiceFromJson.weather == "rainy"


def test_writeTimeServiceToFile():
    # prepare
    import tempfile

    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    timeService = createTimeService()
    timeService.time = 15
    timeService.day = 10
    timeService.weather = "stormy"

    # call
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
        timeServiceJsonReaderWriter.writeTimeServiceToFile(timeService, f)
        temp_file_path = f.name

    # check - read back the file and verify
    with open(temp_file_path, "r") as f:
        timeServiceJson = json.load(f)

    assert timeServiceJson["time"] == 15
    assert timeServiceJson["day"] == 10
    assert timeServiceJson["weather"] == "stormy"

    # cleanup
    import os

    os.remove(temp_file_path)


def test_readTimeServiceFromFile():
    # prepare
    import tempfile

    timeServiceJson = {"time": 12, "day": 5, "weather": "rainy"}

    # Write test data to temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(timeServiceJson, f)
        temp_file_path = f.name

    # call
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    player = Player()
    stats = Stats()
    with open(temp_file_path, "r") as f:
        timeService = timeServiceJsonReaderWriter.readTimeServiceFromFile(
            f, player, stats
        )

    # check
    assert timeService.time == 12
    assert timeService.day == 5
    assert timeService.weather == "rainy"

    # cleanup
    import os

    os.remove(temp_file_path)


def test_createTimeServiceFromJson_missingAllFields_usesDefaults():
    # prepare - a corrupt/partial save with no recognizable fields
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    player = Player()
    stats = Stats()
    timeServiceJson = {}

    # call - must not raise KeyError
    timeService = timeServiceJsonReaderWriter.createTimeServiceFromJson(
        timeServiceJson, player, stats
    )

    # check - all fields fall back to the TimeService() default
    defaults = TimeService(player, stats)
    assert timeService.time == defaults.time
    assert timeService.day == defaults.day
    assert timeService.weather == defaults.weather


def test_createTimeServiceFromJson_outOfRangeTime_raisesValidationError():
    # prepare - a syntactically valid but corrupted save (schemas/timeService.json
    # caps time at 23)
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    player = Player()
    stats = Stats()
    timeServiceJson = {"time": 99, "day": 5}

    # call/check
    with pytest.raises(ValidationError):
        timeServiceJsonReaderWriter.createTimeServiceFromJson(
            timeServiceJson, player, stats
        )


def test_createTimeServiceFromJson_unknownWeather_raisesValidationError():
    # prepare - a corrupted save with a weather value outside the schema's enum
    timeServiceJsonReaderWriter = createTimeServiceJsonReaderWriter()
    player = Player()
    stats = Stats()
    timeServiceJson = {"time": 8, "day": 5, "weather": "sunny_with_dragons"}

    # call/check
    with pytest.raises(ValidationError):
        timeServiceJsonReaderWriter.createTimeServiceFromJson(
            timeServiceJson, player, stats
        )
