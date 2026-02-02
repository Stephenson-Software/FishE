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
            [
                {
                    "question": "How do I fish at the docks?",
                    "response": "Fishing is what this village is all about! You need at least 10 energy to fish. "
                               "When you cast your line, you'll spend several random hours (1-10) fishing. "
                               "Each hour uses 10 energy. When a fish bites, press Enter fast - within 2 seconds! "
                               "Your reaction time matters. The more successful catches, the more fish you'll get. "
                               "Don't worry if you miss a few - you'll still catch at least one fish if you tried!"
                },
                {
                    "question": "What other locations can I visit?",
                    "response": "From the docks, you can get to anywhere in the village! "
                               "There's your home - that's where you sleep to restore energy. "
                               "Gilbert's shop is where you sell fish and buy better bait. "
                               "The tavern is run by Old Tom - gambling and drinks there. "
                               "And the bank, where Margaret will keep your money safe and even give you interest!"
                },
                {
                    "question": "Tell me about energy and rest.",
                    "response": "Energy is your lifeblood as a fisherman! You start each day with it, "
                               "and fishing uses it up - 10 energy per hour of fishing. "
                               "When you're running low, head home and sleep. That'll restore you for the next day. "
                               "The game keeps track of time - each action moves the clock forward. "
                               "Plan your day wisely!"
                },
                {
                    "question": "What makes a good fisherman?",
                    "response": "Patience and quick reflexes! When that fish bites, you gotta be ready. "
                               "Invest in better bait from Gilbert - it makes a huge difference. "
                               "Fish when you have energy, sell regularly, and save your money. "
                               "The sea has its rhythms - you'll learn them in time. "
                               "And remember: it's not just about catching fish, it's about enjoying the life!"
                }
            ]
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

        successfulCatches = 0
        totalAttempts = 0
        
        for i in range(hours):
            print("><> ")
            sys.stdout.flush()
            time.sleep(0.5)
            
            # Interactive minigame: player must press Enter at the right moment
            print("A fish is biting! Press Enter quickly! ")
            sys.stdout.flush()
            
            startTime = time.time()
            try:
                input()
                reactionTime = time.time() - startTime
                
                # Success if pressed within 2 seconds
                if reactionTime <= 2.0:
                    successfulCatches += 1
                    print("Got it! ")
                else:
                    print("Too slow... ")
            except (KeyboardInterrupt, EOFError):
                print("Missed! ")
            
            sys.stdout.flush()
            totalAttempts += 1
            
            self.stats.hoursSpentFishing += 1
            self.timeService.increaseTime()
            self.player.energy -= 10  # Consume 10 energy per hour

        # Calculate fish caught based on success rate
        baseFish = random.randint(1, 10)
        if totalAttempts > 0:
            successRate = successfulCatches / totalAttempts
            fishToAdd = int(baseFish * successRate * self.player.fishMultiplier)
        else:
            fishToAdd = 0
            
        # Ensure at least 1 fish if player attempted
        if fishToAdd == 0 and totalAttempts > 0:
            fishToAdd = 1
            
        self.player.fishCount += fishToAdd
        self.stats.totalFishCaught += fishToAdd

        if fishToAdd == 1:
            self.currentPrompt.text = "Nice catch!"
        else:
            self.currentPrompt.text = "You caught %d fish! It only took %d hours! Success rate: %d%%" % (
                fishToAdd,
                hours,
                int((successfulCatches / totalAttempts * 100) if totalAttempts > 0 else 0)
            )

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
