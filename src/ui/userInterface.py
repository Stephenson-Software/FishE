from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class UserInterface:
    def __init__(self, currentPrompt: Prompt, timeService: TimeService, player: Player):
        self.currentPrompt = currentPrompt
        self.timeService = timeService
        self.player = player

        self.prompt = "Make your choice!"
        self.optionList = []

        self.times = {
            0: "12:00 AM",
            1: "1:00 AM",
            2: "2:00 AM",
            3: "3:00 AM",
            4: "4:00 AM",
            5: "5:00 AM",
            6: "6:00 AM",
            7: "7:00 AM",
            8: "8:00 AM",
            9: "9:00 AM",
            10: "10:00 AM",
            11: "11:00 AM",
            12: "12:00 PM",
            13: "1:00 PM",
            14: "2:00 PM",
            15: "3:00 PM",
            16: "4:00 PM",
            17: "5:00 PM",
            18: "6:00 PM",
            19: "7:00 PM",
            20: "8:00 PM",
            21: "9:00 PM",
            22: "10:00 PM",
            23: "11:00 PM",
        }

    def lotsOfSpace(self):
        print("\n" * 20)

    def divider(self):
        print("\n")
        print("-" * 75)
        print("\n")

    def showOptions(
        self,
        descriptor,
        optionList,
    ):
        while True:
            self.lotsOfSpace()
            self.divider()
            print(" " + descriptor)
            self.divider()
            print(" Day %d" % self.timeService.day)
            print(" | " + self.times[self.timeService.time])
            print(" | Money: $%d" % self.player.money)
            print(" | Fish: %d" % self.player.fishCount)
            print(" | Energy: %d" % self.player.energy)
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

    def showDialogue(self, text):
        self.lotsOfSpace()
        self.divider()
        print(text)
        self.divider()
        input(" [ CONTINUE ]")
        self.currentPrompt.text = "What would you like to do?"
