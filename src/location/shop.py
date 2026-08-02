from location.enum.locationType import LocationType
from location import docks
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC
from npc import villagers
from fish import fish
from business import boats
from business import business
from business import export
from progression import progression


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


def _cheapestAndPriciestFish():
    """The catalogue's cheapest and priciest species, by sale bounds - used to
    quote a true price range in dialogue instead of a hardcoded one (#144)."""
    cheapest = min(fish.FISH_TYPES, key=lambda fishType: fishType["minValue"])
    priciest = max(fish.FISH_TYPES, key=lambda fishType: fishType["maxValue"])
    return cheapest, priciest


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
                    "I may not fish much anymore, but I know good gear when I see it!",
                },
                {
                    "question": "What do you sell here?",
                    "response": self._sellPitchDialogue,
                },
                {
                    "question": "How does fishing work?",
                    "response": self._howFishingWorksDialogue,
                },
                {
                    "question": "Tell me about the bait upgrades.",
                    "response": "Starting bait is decent, but my premium bait? That's where the magic happens! "
                    "Each upgrade increases your fish multiplier by 1. So if you normally catch 5 fish, "
                    "with a 2x multiplier you'll catch 10! The bait gets more expensive each time - "
                    "starts at one price then increases by 25% with each purchase. "
                    "But serious fishermen know it's the best investment you can make!",
                },
                {
                    "question": "Any tips for selling fish?",
                    "response": self._sellingTipsDialogue,
                },
                {
                    "question": "Have you noticed my crew hauling in fish?",
                    "response": self._crewDialogue,
                },
                {
                    # Unlocked by hiring villagers - see NPC.get_dialogue_options.
                    "question": "Do my crew shop here?",
                    "response": self._crewCustomerDialogue,
                    "condition": lambda: bool(self.player.hiredWorkers),
                },
                {
                    # Only worth asking once the player has a boat that can
                    # actually reach the other villages.
                    "question": "Why can't you buy my whole catch?",
                    "response": self._dailyBudgetDialogue,
                    "condition": lambda: export.canExport(self.player),
                },
            ],
        )
        # Daily budget for buying fish; refills when a new day begins.
        self.money = SHOP_DAILY_BUDGET
        self.lastRefillDay = self.timeService.day

    def _sellPitchDialogue(self):
        """Gilbert's pitch on fish prices, quoting the catalogue's actual
        cheapest and priciest species so it can't drift from it (#144)."""
        cheapest, priciest = _cheapestAndPriciestFish()
        return (
            "I deal in all things fishing! I'll buy any fish you catch - the price "
            "varies by species, anywhere from $%d for a %s up to $%d for a %s. "
            "I also sell better bait that'll help you catch more fish. "
            "The price goes up each time you upgrade, but trust me, it's worth it! "
            "Better bait means more fish, and more fish means more money!"
            % (cheapest["minValue"], cheapest["name"], priciest["maxValue"], priciest["name"])
        )

    def _sellingTipsDialogue(self):
        """Gilbert's selling tips, quoting the same catalogue-derived range as
        _sellPitchDialogue so what you catch is framed as mattering."""
        cheapest, priciest = _cheapestAndPriciestFish()
        return (
            "Well, the price per fish depends on what you land - anywhere from $%d "
            "for a %s up to $%d for a %s, so what you catch matters as much as how much! "
            "I'd say don't hoard your fish too long - sell regularly to keep money flowing. "
            "Use that money to buy better bait, which helps you catch more, which means more money! "
            "It's a beautiful cycle, really. And don't forget to save some money at the bank!"
            % (cheapest["minValue"], cheapest["name"], priciest["maxValue"], priciest["name"])
        )

    def _howFishingWorksDialogue(self):
        """Gilbert's explanation of the catch timing minigame, quoting the
        player's actual reaction window - it widens with rod level (#145)."""
        window = docks.REACTION_BASE_WINDOW + (
            self.player.rodLevel - 1
        ) * docks.ROD_WINDOW_STEP
        return (
            "Ah, fishing! Head down to the docks when you've got some energy. "
            "You'll spend a few hours out there, and each hour costs 10 energy. "
            "When a fish bites, you need to press Enter quickly - you've got about "
            "%.1f seconds right now, and a better rod from me widens that window. "
            "React slower and you'll still land something, just less of it. "
            "Better bait from my shop will multiply your catch!" % window
        )

    def _crewDialogue(self):
        """Gilbert's take on the player's fishing business, staged by whether
        there's a crew hauling in fish at all and how much they bring in."""
        if not self.player.hasBoat or self.player.workers == 0:
            return (
                "Can't say I have! Get yourself a boat and a crew down at the "
                "docks - Sam will set you up. Then you'll really see the fish "
                "pile in."
            )
        dailyCatch = boats.fleetDailyCatch(self.player)
        return (
            "That I have! Word is your crew hauls in about %d fish a day. "
            "Keep that up and I might need a bigger vault!" % dailyCatch
        )

    def _crewCustomerDialogue(self):
        """Gilbert's shopkeeper's-eye view of the villagers on the player's
        payroll - he sees them across the counter, not on the water."""
        crew = self.player.hiredWorkers
        if len(crew) == 1:
            return (
                "%s does, aye - in here every few days for tackle. A hand "
                "with wages in their pocket is a customer, and I've you to "
                "thank for that." % crew[0]
            )
        return (
            "They do! %s are all through that door regular now. Whole crews "
            "spend better than lone fishermen ever did - keep hiring and I'll "
            "have to widen the aisles." % villagers.joinNames(crew)
        )

    def _dailyBudgetDialogue(self):
        """Gilbert on his own daily budget, and the export markets it pushes a
        big producer toward. He'd rather keep the business, but he'd rather
        the player kept fishing than let a hoard rot on the dock."""
        markets = export.availableMarkets(self.player)
        names = villagers.joinNames([market["name"] for market in markets])
        return (
            "Because there's only so much coin in that drawer, and only so "
            "many mouths in this village to eat what I buy! I take about $%d "
            "of fish a day and then I'm done until morning. A boat like yours "
            "can carry a hold out to %s - they'll pay over my price, though "
            "the freight'll sting. Don't be a stranger, mind."
            % (SHOP_DAILY_BUDGET, names)
        )

    def run(self):
        # Selling is the whole reason a new player walks up the hill; the gear
        # on the walls is revealed later (see src/progression), so options and
        # actions are built as a pair rather than dispatched on a fixed number.
        li = ["Sell Fish"]
        actions = ["sell"]
        if progression.isUnlocked(self.stats, progression.BAIT):
            li.append("Buy Better Bait ( $%.2f )" % self.player.priceForBait)
            actions.append("bait")
        if progression.isUnlocked(self.stats, progression.ROD):
            li.append("Buy Better Rod ( $%.2f )" % rodUpgradeCost(self.player.rodLevel))
            actions.append("rod")
        if progression.isUnlocked(self.stats, progression.TALK):
            li.append("Talk to %s" % self.npc.name)
            actions.append("talk")
        li.append("Go to Docks")
        actions.append("docks")

        input = self.userInterface.showOptions(
            "The shopkeeper winks at you as you behold his collection of fishing poles.",
            li,
        )
        action = actions[int(input) - 1]

        if action == "sell":
            self.sellFish()
            return LocationType.SHOP
        elif action == "bait":
            self.buyBetterBait()
            return LocationType.SHOP
        elif action == "rod":
            self.buyBetterRod()
            return LocationType.SHOP
        elif action == "talk":
            self.talkToNPC()
            return LocationType.SHOP
        elif action == "docks":
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

        # One entry per held fish, most valuable species first, so the best
        # fish are cashed in before the shop's daily budget runs out; any
        # unaffordable leftovers stay in the inventory for another day.
        queue = fish.bestFirst(self.player.fishByType, self.player.fishCount)

        earned = 0.0
        for species in queue:
            value = fish.fishValue(species)
            if not self.player.operatorMode:
                if self.money < value:
                    break  # shop is out of money for today
                self.money -= value
            self.player.money += value
            self.stats.totalMoneyMade += value
            earned += value
            self.player.removeFish(species)

        if self.player.fishCount > 0:
            self.currentPrompt.text = (
                "Sold fish for $%.2f, but the shop is out of money for today. "
                "%s" % (earned, self._leftoverAdvice())
            )
        else:
            self.currentPrompt.text = "You sold your fish for $%.2f!" % earned

    def _leftoverAdvice(self):
        """What to do with the fish the shop couldn't afford. Once the player
        has a boat that can make the crossing, pointing them at the export
        markets beats telling them to keep waiting a day at a time."""
        if export.canExport(self.player):
            return (
                "Come back tomorrow for the rest, or ship them out from the "
                "docks - the other villages have no daily limit."
            )
        return "Come back tomorrow for the rest."

    def buyBetterBait(self):
        if self.player.fishMultiplier >= MAX_FISH_MULTIPLIER:
            self.currentPrompt.text = "Your bait is already the best money can buy!"
        elif not self.player.canAfford(self.player.priceForBait):
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.fishMultiplier += 1
            self.player.spendMoney(self.player.priceForBait)

            self.player.priceForBait = self.player.priceForBait * 1.25
            self.currentPrompt.text = "You bought some better bait!"

    def buyBetterRod(self):
        cost = rodUpgradeCost(self.player.rodLevel)
        if self.player.rodLevel >= MAX_ROD_LEVEL:
            self.currentPrompt.text = "Your rod is already the finest in the village!"
        elif not self.player.canAfford(cost):
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.rodLevel += 1
            self.player.spendMoney(cost)
            self.currentPrompt.text = "You bought a better fishing rod!"

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
