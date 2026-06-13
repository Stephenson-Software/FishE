from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC
from fish import fish


# Upper bound on fishMultiplier so bait upgrades stop being an infinite power
# climb: past this point "Buy Better Bait" is refused with a message.
MAX_FISH_MULTIPLIER = 10

# Rod upgrades are a second, distinct progression axis from bait: bait raises
# yield (fishMultiplier), the rod widens the catch reaction window (see Docks).
# The cost to reach the next level scales with the current level, so only the
# level needs to be stored.
ROD_BASE_PRICE = 75
MAX_ROD_LEVEL = 10

# The shop has a limited pool of money for buying fish that refills each new day.
# It comfortably covers a normal day's catch but can be exhausted by a very large
# haul, so massive hoards must be sold over several days (and the bank/business
# give somewhere to put wealth in the meantime).
SHOP_DAILY_BUDGET = 750


def rodUpgradeCost(rodLevel):
    return ROD_BASE_PRICE * rodLevel


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
        self.npc = NPC(
            "Gilbert the Shopkeeper",
            "I've been running this shop for thirty years, ever since I inherited it from my father. "
            "I've seen many fishermen come and go, but the best ones always come back for quality bait. "
            "I may not fish much anymore, but I know good gear when I see it!",
            [
                {
                    "question": "Tell me about yourself.",
                    "response": "I've been running this shop for thirty years, ever since I inherited it from my father. "
                               "I've seen many fishermen come and go, but the best ones always come back for quality bait. "
                               "I may not fish much anymore, but I know good gear when I see it!"
                },
                {
                    "question": "What do you sell here?",
                    "response": "I deal in all things fishing! I'll buy any fish you catch - the price varies, "
                               "but you can expect $3 to $5 per fish. I also sell better bait that'll help you catch more fish. "
                               "The price goes up each time you upgrade, but trust me, it's worth it! "
                               "Better bait means more fish, and more fish means more money!"
                },
                {
                    "question": "How does fishing work?",
                    "response": "Ah, fishing! Head down to the docks when you've got some energy. "
                               "You'll spend a few hours out there, and each hour costs 10 energy. "
                               "When a fish bites, you need to press Enter quickly - within 2 seconds! "
                               "Your success rate determines how many fish you catch. "
                               "Better bait from my shop will multiply your catch!"
                },
                {
                    "question": "Tell me about the bait upgrades.",
                    "response": "Starting bait is decent, but my premium bait? That's where the magic happens! "
                               "Each upgrade increases your fish multiplier by 1. So if you normally catch 5 fish, "
                               "with a 2x multiplier you'll catch 10! The bait gets more expensive each time - "
                               "starts at one price then increases by 25% with each purchase. "
                               "But serious fishermen know it's the best investment you can make!"
                },
                {
                    "question": "Any tips for selling fish?",
                    "response": "Well, the price per fish is random between $3 and $5, so sometimes you get lucky! "
                               "I'd say don't hoard your fish too long - sell regularly to keep money flowing. "
                               "Use that money to buy better bait, which helps you catch more, which means more money! "
                               "It's a beautiful cycle, really. And don't forget to save some money at the bank!"
                }
            ]
        )
        # Daily budget for buying fish; refills when a new day begins.
        self.money = SHOP_DAILY_BUDGET
        self.lastRefillDay = self.timeService.day

    def run(self):
        li = [
            "Sell Fish",
            "Buy Better Bait ( $%.2f )" % self.player.priceForBait,
            "Buy Better Rod ( $%.2f )" % rodUpgradeCost(self.player.rodLevel),
            "Talk to %s" % self.npc.name,
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
            self.buyBetterRod()
            return LocationType.SHOP
        elif input == "4":
            self.talkToNPC()
            return LocationType.SHOP
        elif input == "5":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def _refillIfNewDay(self):
        if self.timeService.day > self.lastRefillDay:
            self.money = SHOP_DAILY_BUDGET
            self.lastRefillDay = self.timeService.day

    def sellFish(self):
        self._refillIfNewDay()

        if self.player.fishCount == 0:
            self.currentPrompt.text = "You have no fish to sell."
            return

        # One entry per held fish. Sell the most valuable species first so the
        # best fish are cashed in before the shop's daily budget runs out; any
        # unaffordable leftovers stay in the inventory for another day.
        if self.player.fishByType:
            queue = []
            for species, count in self.player.fishByType.items():
                queue.extend([species] * count)
            queue.sort(
                key=lambda s: (fish.getFishType(s) or {}).get("maxValue", 0),
                reverse=True,
            )
        else:
            # Legacy save with only an aggregate count (no species breakdown).
            queue = [None] * self.player.fishCount

        earned = 0.0
        for species in queue:
            value = fish.fishValue(species)
            if self.money < value:
                break  # shop is out of money for today
            self.money -= value
            self.player.money += value
            self.stats.totalMoneyMade += value
            earned += value
            self._removeOneFish(species)

        if self.player.fishCount > 0:
            self.currentPrompt.text = (
                "Sold fish for $%.2f, but the shop is out of money for today. "
                "Come back tomorrow for the rest." % earned
            )
        else:
            self.currentPrompt.text = "You sold your fish for $%.2f!" % earned

    def _removeOneFish(self, species):
        self.player.fishCount -= 1
        if species is None:
            return
        self.player.fishByType[species] -= 1
        if self.player.fishByType[species] == 0:
            del self.player.fishByType[species]

    def buyBetterBait(self):
        if self.player.fishMultiplier >= MAX_FISH_MULTIPLIER:
            self.currentPrompt.text = "Your bait is already the best money can buy!"
        elif self.player.money < self.player.priceForBait:
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.fishMultiplier += 1
            self.player.money -= self.player.priceForBait

            self.player.priceForBait = self.player.priceForBait * 1.25
            self.currentPrompt.text = "You bought some better bait!"

    def buyBetterRod(self):
        cost = rodUpgradeCost(self.player.rodLevel)
        if self.player.rodLevel >= MAX_ROD_LEVEL:
            self.currentPrompt.text = "Your rod is already the finest in the village!"
        elif self.player.money < cost:
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.rodLevel += 1
            self.player.money -= cost
            self.currentPrompt.text = "You bought a better fishing rod!"

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
