import random
from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC


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

    def run(self):
        li = [
            "Sell Fish",
            "Buy Better Bait ( $%d )" % self.player.priceForBait,
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
            self.talkToNPC()
            return LocationType.SHOP
        elif input == "4":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def sellFish(self):
        moneyToAdd = self.player.fishCount * random.randint(3, 5)
        self.player.money += moneyToAdd
        self.stats.totalMoneyMade += moneyToAdd
        self.player.fishCount = 0

        self.currentPrompt.text = "You sold all of your fish!"

    def buyBetterBait(self):
        if self.player.money < self.player.priceForBait:
            self.currentPrompt.text = "You don't have enough money!"
        else:
            self.player.fishMultiplier += 1
            self.player.money -= self.player.priceForBait

            self.player.priceForBait = self.player.priceForBait * 1.25
            self.currentPrompt.text = "You bought some better bait!"

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
