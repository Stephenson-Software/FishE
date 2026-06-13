import json
from player.player import Player


class PlayerJsonReaderWriter:
    def createJsonFromPlayer(self, player):
        return {
            "fishCount": player.fishCount,
            "fishMultiplier": player.fishMultiplier,
            "money": player.money,
            "moneyInBank": player.moneyInBank,
            "priceForBait": player.priceForBait,
            "energy": player.energy,
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
        return player

    def writePlayerToFile(self, player, jsonFile):
        playerJson = self.createJsonFromPlayer(player)
        json.dump(playerJson, jsonFile)

    def readPlayerFromFile(self, jsonFile):
        playerJson = json.load(jsonFile)
        return self.createPlayerFromJson(playerJson)
