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
from business import business
from housing import housing


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
                    "The sea provides for those who respect her!",
                },
                {
                    "question": "How do I fish at the docks?",
                    "response": "Fishing is what this village is all about! You need at least 10 energy to fish. "
                    "When you cast your line, you'll spend several random hours (1-10) fishing. "
                    "Each hour uses 10 energy. When a fish bites, press Enter fast - within 2 seconds! "
                    "Your reaction time matters. The more successful catches, the more fish you'll get. "
                    "Don't worry if you miss a few - you'll still catch at least one fish if you tried!",
                },
                {
                    "question": "What other locations can I visit?",
                    "response": "From the docks, you can get to anywhere in the village! "
                    "There's your home - that's where you sleep to restore energy. "
                    "Gilbert's shop is where you sell fish and buy better bait. "
                    "The tavern is run by Old Tom - gambling and drinks there. "
                    "And the bank, where Margaret will keep your money safe and even give you interest!",
                },
                {
                    "question": "Tell me about energy and rest.",
                    "response": "Energy is your lifeblood as a fisherman! You start each day with it, "
                    "and fishing uses it up - 10 energy per hour of fishing. "
                    "When you're running low, head home and sleep. That'll restore you for the next day. "
                    "The game keeps track of time - each action moves the clock forward. "
                    "Plan your day wisely!",
                },
                {
                    "question": "What makes a good fisherman?",
                    "response": "Patience and quick reflexes! When that fish bites, you gotta be ready. "
                    "Invest in better bait from Gilbert - it makes a huge difference. "
                    "Fish when you have energy, sell regularly, and save your money. "
                    "The sea has its rhythms - you'll learn them in time. "
                    "And remember: it's not just about catching fish, it's about enjoying the life!",
                },
                {
                    "question": "How's my fishing business doing?",
                    "response": self._businessDialogue,
                },
            ],
        )

    def run(self):
        li = [
            "Fish",
            "Talk to %s" % self.npc.name,
            "Go Home",
            "Go to Shop",
            "Go to Tavern",
            "Go to Bank",
            "Manage Boat & Crew",
        ]
        if self.player.hasBoat and self.player.businessName:
            descriptor = (
                "%s is docked and ready for the day." % self.player.businessName
            )
        else:
            descriptor = "You breathe in the fresh air. Salty."
        input = self.userInterface.showOptions(descriptor, li)

        if input == "1":
            if self.player.hasEnergy(10):
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

        elif input == "7":
            self.manageBusiness()
            return LocationType.DOCKS

    def _businessDialogue(self):
        """Sam's take on the player's fishing business, staged by boat tier and
        crew size so it reflects real progress rather than being fixed text."""
        if not self.player.hasBoat:
            return (
                "No boat yet, eh? Once you've got one, I can help you find "
                "good hands to hire. A crew changes everything!"
            )
        if self.player.workers == 0:
            starter = business.tierInfo(business.currentTier(self.player))
            return (
                "A %s of your own! Now you just need to hire a crew to get "
                "it earning." % starter["name"]
            )
        tier = business.currentTier(self.player)
        name = self.player.businessName or "your business"
        if tier == 1:
            return (
                "%s is off to a solid start with that Rowboat crew. Save up "
                "and you could afford a bigger boat before long." % name
            )
        if tier == 2:
            return (
                "A Trawler! %s is really coming along. I've seen a lot of "
                "fishermen never make it past a rowboat." % name
            )
        return (
            "A whole Fishing Fleet under %s? You're the talk of the docks! "
            "Never thought I'd see an outfit like that around here." % name
        )

    def _businessStatus(self):
        if not self.player.hasBoat:
            starter = business.tierInfo(1)
            return (
                "You have no boat. A boat lets you hire a crew that brings in a "
                "passive catch each day. A %s costs $%d."
                % (starter["name"], starter["cost"])
            )
        tier = business.currentTier(self.player)
        info = business.tierInfo(tier)
        name = self.player.businessName or "Unnamed Fishing Co."
        return (
            "%s - %s (tier %d/%d)\n"
            "Crew: %d/%d workers. Each catches %d fish per day for $%d in "
            "wages, paid automatically every new day."
            % (
                name,
                info["name"],
                tier,
                len(business.BOAT_TIERS),
                self.player.workers,
                info["maxWorkers"],
                info["fishPerDay"],
                business.WORKER_DAILY_WAGE,
            )
        )

    def manageBusiness(self):
        while True:
            options = []
            actions = []
            if not self.player.hasBoat:
                starter = business.tierInfo(1)
                options.append("Buy a %s ($%d)" % (starter["name"], starter["cost"]))
                actions.append("buy_boat")
            else:
                tier = business.currentTier(self.player)
                info = business.tierInfo(tier)
                if self.player.workers < info["maxWorkers"]:
                    options.append(
                        "Hire a Worker (+%d fish/day for $%d/day)"
                        % (info["fishPerDay"], business.WORKER_DAILY_WAGE)
                    )
                    actions.append("hire")
                if self.player.workers > 0:
                    options.append("Dismiss a Worker")
                    actions.append("dismiss")
                if tier < len(business.BOAT_TIERS):
                    nextInfo = business.tierInfo(tier + 1)
                    options.append(
                        "Upgrade to a %s ($%d)" % (nextInfo["name"], nextInfo["cost"])
                    )
                    actions.append("upgrade_boat")
                options.append("Rename Business")
                actions.append("rename")
            options.append("Back")
            actions.append("back")

            choice = int(
                self.userInterface.showOptions(self._businessStatus(), options)
            )
            action = actions[choice - 1]

            if action == "buy_boat":
                starter = business.tierInfo(1)
                if self.player.canAfford(starter["cost"]):
                    self.player.spendMoney(starter["cost"])
                    self.player.hasBoat = True
                    self.player.boatTier = 1
                    self.currentPrompt.text = (
                        "You bought a %s! Now hire a crew." % starter["name"]
                    )
                else:
                    self.currentPrompt.text = "You can't afford a boat yet."
            elif action == "hire":
                self.player.workers += 1
                self.stats.totalWorkersHired += 1
                self.currentPrompt.text = (
                    "You hired a worker. They'll fish each day for their wage."
                )
            elif action == "dismiss":
                self.player.workers -= 1
                self.currentPrompt.text = "You let a worker go."
            elif action == "upgrade_boat":
                tier = business.currentTier(self.player)
                nextInfo = business.tierInfo(tier + 1)
                if self.player.canAfford(nextInfo["cost"]):
                    self.player.spendMoney(nextInfo["cost"])
                    self.player.boatTier = tier + 1
                    self.currentPrompt.text = "You upgraded to a %s!" % nextInfo["name"]
                else:
                    self.currentPrompt.text = "You can't afford that upgrade yet."
            elif action == "rename":
                self._renameBusiness()
            elif action == "back":
                self.currentPrompt.text = "What would you like to do?"
                return

    def _renameBusiness(self):
        name = self.userInterface.promptForText(
            "What would you like to name your fishing business?"
        )
        name = (name or "").strip()[:40]
        if name:
            self.player.businessName = name
            self.currentPrompt.text = "Your business is now known as %s!" % name
        else:
            self.currentPrompt.text = "Never mind - the name stays %s." % (
                self.player.businessName or "Unnamed Fishing Co."
            )

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
        if not self.player.hasEnergy(energy_needed):
            # Fish for as many hours as energy allows
            hours = self.player.energy // 10
            if hours == 0:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return

        # A better rod widens the timing window, making catches more forgiving.
        reactionWindow = (
            REACTION_BASE_WINDOW + (self.player.rodLevel - 1) * ROD_WINDOW_STEP
        )

        # One timing challenge per cast (not a pass/fail repeated every hour):
        # how quickly you set the hook maps to a catch-quality tier. The active
        # front-end captures and times the reaction, so this works in any UI.
        reactionTime = self.userInterface.timedKeyPress(
            "A fish is biting! React the moment you feel a bite!"
        )

        if reactionTime <= reactionWindow / 2:
            quality, qualityLabel = 1.0, "A perfect hook!"
        elif reactionTime <= reactionWindow:
            quality, qualityLabel = 0.6, "A solid hook."
        else:
            quality, qualityLabel = 0.25, "The fish nearly got away."

        # Spend the fishing hours: time passes and energy is consumed. A long
        # enough trip can cross a day boundary (and so, e.g., miss a rent
        # payment) without the player ever seeing a "new day" screen, so
        # track that across the loop to mention it in the trip's own report.
        evicted = False
        for i in range(hours):
            self.stats.hoursSpentFishing += 1
            if self.timeService.increaseTime()["evicted"]:
                evicted = True
            self.player.spendEnergy(10)  # Consume 10 energy per hour

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

        if evicted:
            self.currentPrompt.text += " " + housing.EVICTION_MESSAGE

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
