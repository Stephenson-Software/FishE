from ui.baseUserInterface import BaseUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class ConsoleUserInterface(BaseUserInterface):
    """Console-based user interface implementation"""
    
    def __init__(self, currentPrompt: Prompt, timeService: TimeService, player: Player):
        super().__init__(currentPrompt, timeService, player)

    def lotsOfSpace(self):
        print("\n" * 20)

    def divider(self):
        print("\n")
        print("-" * 75)
        print("\n")

    def showOptions(self, descriptor, optionList):
        while True:
            self.lotsOfSpace()
            self.divider()
            print(" " + descriptor)
            self.divider()
            print(" Day %d" % self.timeService.day)
            print(" | " + self.times[self.timeService.time])
            print(" | Money: $%d" % self.player.money)
            print(" | Fish: %d" % self.player.fishCount)
            print("\n " + self.currentPrompt.text)
            self.divider()
            self.n = 1
            self.listOfN = []
            for option in optionList:
                print(" [%d] %s" % (self.n, option))
                self.listOfN.append("%d" % self.n)
                self.n += 1

            choice = input("\n> ")
            for i in self.listOfN:
                if choice == i:
                    return choice

            self.currentPrompt.text = "Try again!"
    
    def cleanup(self):
        # Console UI doesn't need cleanup
        pass