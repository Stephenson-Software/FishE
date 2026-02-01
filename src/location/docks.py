import random
import sys
import time

from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC


# @author Daniel McCoy Stephenson
class Docks:
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
        self.npc = NPC(
            "Sam the Dock Worker",
            "Been working these docks since I was knee-high to a grasshopper. "
            "My pa was a fisherman, and his pa before him. I help maintain the boats and docks, "
            "and I've learned a thing or two about fishing over the years. "
            "The sea provides for those who respect her!",
        )

    def run(self):
        li = ["Fish", "Talk to %s" % self.npc.name, "Go Home", "Go to Shop", "Go to Tavern", "Go to Bank"]
        input = self.userInterface.showOptions(
            "You breathe in the fresh air. Salty.", li
        )

        if input == "1":
            if self.player.energy >= 10:
                self.fish()
                return LocationType.DOCKS
            else:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return LocationType.DOCKS

        elif input == "2":
            self.talkToNPC()
            return LocationType.DOCKS

        elif input == "3":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.HOME

        elif input == "4":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.SHOP

        elif input == "5":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.TAVERN

        elif input == "6":
            self.currentPrompt.text = (
                "What would you like to do? Money in Bank: $%.2f"
                % self.player.moneyInBank
            )
            return LocationType.BANK

    def fish(self):
        self.userInterface.lotsOfSpace()
        self.userInterface.divider()

        print("Fishing... "),
        sys.stdout.flush()
        time.sleep(1)

        hours = random.randint(1, 10)

        # Check if player has enough energy for all hours
        energy_needed = hours * 10
        if self.player.energy < energy_needed:
            # Fish for as many hours as energy allows
            hours = self.player.energy // 10
            if hours == 0:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return

        for i in range(hours):
            print("><> ")
            sys.stdout.flush()
            time.sleep(0.5)
            self.stats.hoursSpentFishing += 1
            self.timeService.increaseTime()
            self.player.energy -= 10  # Consume 10 energy per hour

        fishToAdd = random.randint(1, 10) * self.player.fishMultiplier
        self.player.fishCount += fishToAdd
        self.stats.totalFishCaught += fishToAdd

        if fishToAdd == 1:
            self.currentPrompt.text = "Nice catch!"
        else:
            self.currentPrompt.text = "You caught %d fish! It only took %d hours!" % (
                fishToAdd,
                hours,
            )

    def talkToNPC(self):
        self.userInterface.showDialogue(self.npc.introduce())
