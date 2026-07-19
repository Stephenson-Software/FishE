import json
from world.timeService import TimeService
from validation.schemaValidator import validate_against_schema

TIME_SERVICE_SCHEMA_PATH = "schemas/timeService.json"


class TimeServiceJsonReaderWriter:
    def createJsonFromTimeService(self, timeService):
        return {"time": timeService.time, "day": timeService.day}

    def createTimeServiceFromJson(self, timeServiceJson, player, stats):
        # Read each field with a fallback to the freshly-constructed
        # TimeService's default, so a save file missing any field loads
        # gracefully instead of raising KeyError (backwards compatibility).
        timeService = TimeService(player, stats)
        timeService.time = timeServiceJson.get("time", timeService.time)
        timeService.day = timeServiceJson.get("day", timeService.day)

        # Validate the resulting values (not the raw input) against the
        # schema - see PlayerJsonReaderWriter.createPlayerFromJson for why.
        validate_against_schema(
            self.createJsonFromTimeService(timeService), TIME_SERVICE_SCHEMA_PATH
        )
        return timeService

    def writeTimeServiceToFile(self, timeService, jsonFile):
        timeServiceJson = self.createJsonFromTimeService(timeService)
        json.dump(timeServiceJson, jsonFile)

    def readTimeServiceFromFile(self, jsonFile, player, stats):
        timeServiceJson = json.load(jsonFile)
        return self.createTimeServiceFromJson(timeServiceJson, player, stats)
