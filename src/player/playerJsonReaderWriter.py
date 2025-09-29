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
        player = Player()
        player.fishCount = playerJson["fishCount"]
        player.fishMultiplier = playerJson["fishMultiplier"]
        player.money = playerJson["money"]
        player.moneyInBank = playerJson["moneyInBank"]
        player.priceForBait = playerJson["priceForBait"]
        player.energy = playerJson.get("energy", 100)  # Default to 100 for backwards compatibility
        return player

    def writePlayerToFile(self, player, jsonFile):
        playerJson = self.createJsonFromPlayer(player)
        json.dump(playerJson, jsonFile)

    def readPlayerFromFile(self, jsonFile):
        playerJson = json.load(jsonFile)
        return self.createPlayerFromJson(playerJson)
