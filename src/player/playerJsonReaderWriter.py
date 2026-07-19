import json
from player.player import Player
from validation.schemaValidator import validate_against_schema

PLAYER_SCHEMA_PATH = "schemas/player.json"


class PlayerJsonReaderWriter:
    def createJsonFromPlayer(self, player):
        return {
            "fishCount": player.fishCount,
            "fishMultiplier": player.fishMultiplier,
            "money": player.money,
            "moneyInBank": player.moneyInBank,
            "priceForBait": player.priceForBait,
            "energy": player.energy,
            "rodLevel": player.rodLevel,
            "fishByType": player.fishByType,
            "hasBoat": player.hasBoat,
            "workers": player.workers,
            "boatTier": player.boatTier,
            "businessName": player.businessName,
            "homeTier": player.homeTier,
            "rentalProperties": player.rentalProperties,
        }

    def createPlayerFromJson(self, playerJson):
        # Read each field with a fallback to the freshly-constructed Player's
        # default, so a save file missing any field loads gracefully instead of
        # raising KeyError (backwards compatibility for older/partial saves).
        player = Player()
        player.fishCount = playerJson.get("fishCount", player.fishCount)
        player.fishMultiplier = playerJson.get("fishMultiplier", player.fishMultiplier)
        player.money = playerJson.get("money", player.money)
        player.moneyInBank = playerJson.get("moneyInBank", player.moneyInBank)
        player.priceForBait = playerJson.get("priceForBait", player.priceForBait)
        player.energy = playerJson.get("energy", player.energy)
        player.rodLevel = playerJson.get("rodLevel", player.rodLevel)
        player.fishByType = playerJson.get("fishByType", player.fishByType)
        player.hasBoat = playerJson.get("hasBoat", player.hasBoat)
        player.workers = playerJson.get("workers", player.workers)
        player.boatTier = playerJson.get("boatTier", player.boatTier)
        player.businessName = playerJson.get("businessName", player.businessName)
        player.homeTier = playerJson.get("homeTier", player.homeTier)
        player.rentalProperties = playerJson.get(
            "rentalProperties", player.rentalProperties
        )

        # Validate the resulting values (not the raw input) against the
        # schema, so a save missing keys still loads via the defaults above
        # (backwards compatibility), while an out-of-range value that was
        # present (e.g. energy: -500) is caught here instead of surfacing as
        # a ValueError deep in game logic later.
        validate_against_schema(self.createJsonFromPlayer(player), PLAYER_SCHEMA_PATH)
        return player

    def writePlayerToFile(self, player, jsonFile):
        playerJson = self.createJsonFromPlayer(player)
        json.dump(playerJson, jsonFile)

    def readPlayerFromFile(self, jsonFile):
        playerJson = json.load(jsonFile)
        return self.createPlayerFromJson(playerJson)
