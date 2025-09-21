import json
from location.shop import Shop
from ui.userInterface import UserInterface
from prompt.prompt import Prompt
from player.player import Player
from stats.stats import Stats
from world.timeService import TimeService


class ShopJsonReaderWriter:
    def createJsonFromShop(self, shop: Shop):
        return {"money": shop.money}

    def createShopFromJson(self, shopJson, userInterface: UserInterface, currentPrompt: Prompt, player: Player, stats: Stats, timeService: TimeService):
        shop = Shop(userInterface, currentPrompt, player, stats, timeService)
        shop.money = shopJson["money"]
        return shop

    def writeShopToFile(self, shop, jsonFile):
        shopJson = self.createJsonFromShop(shop)
        json.dump(shopJson, jsonFile)

    def readShopFromFile(self, jsonFile, userInterface: UserInterface, currentPrompt: Prompt, player: Player, stats: Stats, timeService: TimeService):
        shopJson = json.load(jsonFile)
        return self.createShopFromJson(shopJson, userInterface, currentPrompt, player, stats, timeService)