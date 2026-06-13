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
from fish import fish


# The catch reaction window widens with the player's rod level, so a better rod
# (bought at the shop) makes the timing minigame more forgiving. Level 1 keeps
# the original 2.0s window.
REACTION_BASE_WINDOW = 2.0
ROD_WINDOW_STEP = 0.5


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
                    "question": "Tell me about yourself.",
                    "response": "Been working these docks since I was knee-high to a grasshopper. "
                               "My pa was a fisherman, and his pa before him. I help maintain the boats and docks, "
                               "and I've learned a thing or two about fishing over the years. "
                               "The sea provides for those who respect her!"
                },
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

    def getTimeOfDayModifier(self, hour):
        """Return (yield factor, flavour label) for fishing at the given hour.

        Fish feed most actively around dawn and dusk and go quiet under the
        midday sun, so the time of day now meaningfully affects the catch."""
        if 5 <= hour <= 8:
            return 1.5, "The dawn bite is on!"
        if 17 <= hour <= 20:
            return 1.5, "The fish are feeding at dusk!"
        if 11 <= hour <= 14:
            return 0.6, "The midday sun keeps the fish deep."
        return 1.0, ""

    def fish(self):
        self.userInterface.lotsOfSpace()
        self.userInterface.divider()

        print("Fishing... "),
        sys.stdout.flush()
        time.sleep(1)

        # Capture the time of day at the start of the trip (the loop advances it).
        timeFactor, timeLabel = self.getTimeOfDayModifier(self.timeService.time)

        hours = random.randint(1, 10)

        # Check if player has enough energy for all hours
        energy_needed = hours * 10
        if self.player.energy < energy_needed:
            # Fish for as many hours as energy allows
            hours = self.player.energy // 10
            if hours == 0:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return

        # A better rod widens the timing window, making catches more forgiving.
        reactionWindow = REACTION_BASE_WINDOW + (self.player.rodLevel - 1) * ROD_WINDOW_STEP

        # One timing challenge per cast (not a pass/fail repeated every hour):
        # how quickly you set the hook maps to a catch-quality tier.
        print("Cast your line... press Enter the moment you feel a bite! ")
        sys.stdout.flush()
        startTime = time.time()
        try:
            input()
            reactionTime = time.time() - startTime
        except (KeyboardInterrupt, EOFError):
            reactionTime = reactionWindow + 1.0  # an aborted input counts as a miss

        if reactionTime <= reactionWindow / 2:
            quality, qualityLabel = 1.0, "A perfect hook!"
        elif reactionTime <= reactionWindow:
            quality, qualityLabel = 0.6, "A solid hook."
        else:
            quality, qualityLabel = 0.25, "The fish nearly got away."

        # Spend the fishing hours: time passes and energy is consumed.
        for i in range(hours):
            self.stats.hoursSpentFishing += 1
            self.timeService.increaseTime()
            self.player.energy -= 10  # Consume 10 energy per hour

        baseFish = random.randint(1, 10)
        fishToAdd = int(baseFish * quality * self.player.fishMultiplier * timeFactor)
        if fishToAdd == 0:
            fishToAdd = 1  # always land at least one fish for the effort

        # Which species you hooked this trip, weighted by rarity.
        fishTypeName = fish.rollFishType()
        self.player.addFish(fishTypeName, fishToAdd)
        self.stats.totalFishCaught += fishToAdd

        self.currentPrompt.text = "You caught %d %s over %d hours! %s" % (
            fishToAdd,
            fishTypeName,
            hours,
            qualityLabel,
        )

        if timeLabel:
            self.currentPrompt.text += " " + timeLabel

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
