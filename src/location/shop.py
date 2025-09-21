import random
from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface


# @author Daniel McCoy Stephenson
class Shop:
    def __init__(
        self,
        userInterface: UserInterface,
        currentPrompt: Prompt,
        player: Player,
        stats: Stats,
        timeService: TimeService,
    ):
        self.userInterface = userInterface
        self.currentPrompt = currentPrompt
        self.player = player
        self.stats = stats
        self.timeService = timeService
        self.money = 1000  # Shop starts with $1000

    def run(self):
        li = [
            "Sell Fish",
            "Buy Better Bait ( $%d )" % self.player.priceForBait,
            "Go to Docks",
        ]
        input = self.userInterface.showOptions(
            "The shopkeeper winks at you as you behold his collection of fishing poles.",
            li,
        )

        if input == "1":
            self.sellFish()
            return LocationType.SHOP
        elif input == "2":
            self.buyBetterBait()
            return LocationType.SHOP
        elif input == "3":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def sellFish(self):
        if self.player.fishCount == 0:
            self.currentPrompt.text = "You don't have any fish to sell!"
            return
            
        moneyToAdd = self.player.fishCount * random.randint(3, 5)
        
        if self.money < moneyToAdd:
            self.currentPrompt.text = "The shop doesn't have enough money to buy all your fish!"
            return
            
        self.player.money += moneyToAdd
        self.stats.totalMoneyMade += moneyToAdd
        self.money -= moneyToAdd
        self.player.fishCount = 0

        self.currentPrompt.text = "You sold all of your fish!"

    def buyBetterBait(self):
        if self.player.money < self.player.priceForBait:
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.fishMultiplier += 1
            self.player.money -= self.player.priceForBait

            self.player.priceForBait = self.player.priceForBait * 1.25
            self.currentPrompt.text = "You bought some better bait!"
