import os
from location import bank, docks, home, shop, tavern
from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from player.playerJsonReaderWriter import PlayerJsonReaderWriter
from stats.statsJsonReaderWriter import StatsJsonReaderWriter
from world.timeServiceJsonReaderWriter import TimeServiceJsonReaderWriter
from location.shopJsonReaderWriter import ShopJsonReaderWriter
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface


# @author Daniel McCoy Stephenson
class FishE:
    def __init__(self):
        self.running = True

        self.playerJsonReaderWriter = PlayerJsonReaderWriter()
        self.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
        self.statsJsonReaderWriter = StatsJsonReaderWriter()
        self.shopJsonReaderWriter = ShopJsonReaderWriter()

        # if save file exists, load it
        if (
            os.path.exists("data/player.json")
            and os.path.getsize("data/player.json") > 0
        ):
            self.loadPlayer()
        else:
            self.player = Player()

        # if save file exists, load it
        if os.path.exists("data/stats.json") and os.path.getsize("data/stats.json") > 0:
            self.loadStats()
        else:
            self.stats = Stats()

        # if save file exists, load it
        if (
            os.path.exists("data/timeService.json")
            and os.path.getsize("data/timeService.json") > 0
        ):
            self.loadTimeService()
        else:
            self.timeService = TimeService(self.player, self.stats)

        self.prompt = Prompt("What would you like to do?")

        self.userInterface = UserInterface(self.prompt, self.timeService, self.player)

        # if save file exists, load it
        if (
            os.path.exists("data/shop.json")
            and os.path.getsize("data/shop.json") > 0
        ):
            self.loadShop()
        else:
            self.shop = shop.Shop(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            )

        self.locations = {
            LocationType.BANK: bank.Bank(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.DOCKS: docks.Docks(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.HOME: home.Home(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.SHOP: self.shop,
            LocationType.TAVERN: tavern.Tavern(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
        }

        self.currentLocation = LocationType.HOME

    def play(self):
        while self.running:
            # change location
            nextLocation = self.locations[self.currentLocation].run()

            if nextLocation == LocationType.NONE:
                self.running = False

            self.currentLocation = nextLocation

            # increase time & save
            self.timeService.increaseTime()
            self.save()

    def save(self):
        # create data directory
        if not os.path.exists("data"):
            os.makedirs("data")

        playerSaveFile = open("data/player.json", "w")
        self.playerJsonReaderWriter.writePlayerToFile(self.player, playerSaveFile)

        timeServiceSaveFile = open("data/timeService.json", "w")
        self.timeServiceJsonReaderWriter.writeTimeServiceToFile(
            self.timeService, timeServiceSaveFile
        )

        statsSaveFile = open("data/stats.json", "w")
        self.statsJsonReaderWriter.writeStatsToFile(self.stats, statsSaveFile)

        shopSaveFile = open("data/shop.json", "w")
        self.shopJsonReaderWriter.writeShopToFile(self.shop, shopSaveFile)

    def loadPlayer(self):
        playerSaveFile = open("data/player.json", "r")
        self.player = self.playerJsonReaderWriter.readPlayerFromFile(playerSaveFile)
        playerSaveFile.close()

    def loadStats(self):
        statsSaveFile = open("data/stats.json", "r")
        self.stats = self.statsJsonReaderWriter.readStatsFromFile(statsSaveFile)
        statsSaveFile.close()

    def loadTimeService(self):
        timeServiceSaveFile = open("data/timeService.json", "r")
        self.timeService = self.timeServiceJsonReaderWriter.readTimeServiceFromFile(
            timeServiceSaveFile, self.player, self.stats
        )
        timeServiceSaveFile.close()

    def loadShop(self):
        shopSaveFile = open("data/shop.json", "r")
        self.shop = self.shopJsonReaderWriter.readShopFromFile(
            shopSaveFile, self.userInterface, self.prompt, self.player, self.stats, self.timeService
        )
        shopSaveFile.close()


if __name__ == "__main__":
    FishE = FishE()
    FishE.play()
