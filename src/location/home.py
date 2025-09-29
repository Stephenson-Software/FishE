from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface


# @author Daniel McCoy Stephenson
class Home:
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

    def run(self):
        li = ["Sleep", "See Stats", "Go to Docks", "Quit"]
        self.input = self.userInterface.showOptions(
            "You sit at home, polishing one of your prized fishing poles.", li
        )

        if self.input == "1":
            self.sleep()
            return LocationType.HOME
        elif self.input == "2":
            self.displayStats()
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.HOME
        elif self.input == "3":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS
        elif self.input == "4":
            return LocationType.NONE

    def sleep(self):
        self.timeService.increaseDay()
        self.player.energy = 100  # Restore full energy when sleeping
        self.currentPrompt.text = "You sleep until the next morning. You feel refreshed!"

    def displayStats(self):
        self.userInterface.lotsOfSpace()
        print("Total Fish Caught: %d" % self.stats.totalFishCaught)
        print("Total Money Made: %d" % self.stats.totalMoneyMade)
        print("Hours Spent Fishing: %d" % self.stats.hoursSpentFishing)
        print("Money Made From Interest: %d" % self.stats.moneyMadeFromInterest)
        print("Times Gotten Drunk: %d" % self.stats.timesGottenDrunk)
        print("Money Lost Gambling: %d" % self.stats.moneyLostFromGambling)
        print("")
        input(" [ CONTINUE ]")
