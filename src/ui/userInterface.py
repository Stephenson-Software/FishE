import sys
import time
from ui.baseUserInterface import BaseUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class UserInterface(BaseUserInterface):
    """The text/console front-end — FishE's default user interface.

    Shared state (prompt, times, header fields) comes from BaseUserInterface;
    this class implements the console rendering/input primitives and a richer
    interactive-dialogue layout."""

    def __init__(self, currentPrompt: Prompt, timeService: TimeService, player: Player):
        super().__init__(currentPrompt, timeService, player)

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
            if self.currentLocationName:
                print(" | Location: " + self.currentLocationName)
            print(" | " + self.times[self.timeService.time])
            print(" | Money: $%.2f" % self.player.money)
            print(" | Fish: %d" % self.player.fishCount)
            print(" | Energy: %d" % self.player.energy)
            if self.player.operatorMode:
                print(" | [OPERATOR MODE]")
            if self.goalProgress:
                print(" | Goal: " + self.goalProgress)
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

    def promptForText(self, promptText):
        self.lotsOfSpace()
        self.divider()
        print(promptText)
        self.divider()
        return input("> ")

    def timedKeyPress(self, message):
        print(message)
        sys.stdout.flush()
        startTime = time.time()
        try:
            input()
            return time.time() - startTime
        except (KeyboardInterrupt, EOFError):
            # No reaction captured — treat it as having missed entirely.
            return float("inf")

    def cleanup(self):
        # The console front-end holds no resources to release.
        pass
