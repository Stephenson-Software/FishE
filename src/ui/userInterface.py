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
    
    def showInteractiveDialogue(self, npc):
        """Shows an interactive dialogue menu with the NPC"""
        while True:
            self.lotsOfSpace()
            self.divider()
            print(f" Talking with {npc.name}")
            self.divider()
            
            # Show dialogue options
            dialogue_options = npc.get_dialogue_options()
            if not dialogue_options:
                # Fallback to simple introduction if no options
                print(npc.introduce())
                self.divider()
                input(" [ CONTINUE ]")
                self.currentPrompt.text = "What would you like to do?"
                break
            
            print(" What would you like to ask?\n")
            option_list = []
            for i, option in enumerate(dialogue_options):
                question = option.get("question", f"Option {i+1}")
                print(f" [{i+1}] {question}")
                option_list.append(str(i+1))
            
            print(f" [{len(option_list)+1}] [Back]")
            option_list.append(str(len(option_list)+1))
            
            choice = input("\n> ")
            
            if choice in option_list:
                choice_idx = int(choice) - 1
                
                # Check if user chose to go back
                if choice_idx == len(dialogue_options):
                    self.currentPrompt.text = "What would you like to do?"
                    break
                
                # Show the response
                response = npc.get_dialogue_response(choice_idx)
                self.lotsOfSpace()
                self.divider()
                print(f" {npc.name}: {response}")
                self.divider()
                input(" [ CONTINUE ]")
            else:
                print(" Invalid choice. Try again!")
                input(" [ CONTINUE ]")
