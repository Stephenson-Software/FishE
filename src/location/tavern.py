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
from business import business


# Dice has 6 equally likely faces, so a correct guess pays 5x the bet to make
# the wager roughly fair (EV ~= 0) instead of the old even-money payout, which
# made gambling a guaranteed long-run loss no rational player would take.
DICE_WIN_MULTIPLIER = 5

# Chances applied while drunk, in order: lose a chunk of money, or instead pick
# up a lucrative rumor. Giving drinking an upside (not just a downside) makes it
# a real risk/reward choice rather than a pure money sink.
DRUNK_LOSS_CHANCE = 0.3
DRUNK_TIP_CHANCE = 0.3


# @author Daniel McCoy Stephenson
class Tavern:
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

        self.currentBet = 0
        self.npc = NPC(
            "Old Tom the Barkeep",
            "I sailed the seven seas for forty years before settling down here. "
            "Lost my leg to a shark near the Caribbean, but I got plenty of stories to make up for it. "
            "These days I pour drinks and listen to folks' troubles. Best job I ever had!",
            [
                {
                    "question": "Tell me about yourself.",
                    "response": "I sailed the seven seas for forty years before settling down here. "
                               "Lost my leg to a shark near the Caribbean, but I got plenty of stories to make up for it. "
                               "These days I pour drinks and listen to folks' troubles. Best job I ever had!"
                },
                {
                    "question": "How do I make money in this village?",
                    "response": "Well now, there's a few ways to fill your pockets around here! "
                               "The most reliable is fishing at the docks - catch some fish and sell 'em at Gilbert's shop. "
                               "You can also try your luck at gambling right here in the tavern, but be warned - "
                               "the dice don't always roll in your favor! And if you're patient, the bank offers "
                               "interest on your savings."
                },
                {
                    "question": "What can I do at the tavern?",
                    "response": "Ah, the tavern! This is the place to unwind after a long day. "
                               "You can get yourself drunk for $10 - though you'll wake up at home with a headache the next day! "
                               "Or if you're feeling lucky, you can gamble with the dice. Place a bet, pick a number from 1 to 6, "
                               "and if the dice matches your choice, you'll double your money!"
                },
                {
                    "question": "Tell me about the other villagers.",
                    "response": "Let me see... There's Gilbert the shopkeeper - been running that shop for thirty years. "
                               "He'll buy your fish and sell you better bait. Then there's Sam down at the docks, "
                               "knows everything about fishing. Margaret at the bank will keep your money safe. "
                               "All good folk, they are!"
                },
                {
                    "question": "Any advice for a newcomer?",
                    "response": "Aye, I've seen many fishermen come through these doors. Here's what I tell 'em all: "
                               "Start small, fish when you have energy, and sell your catch regularly. "
                               "Don't gamble away all your coin - save some at the bank. "
                               "And remember, better bait means better catches. Take your time and enjoy the village!"
                },
                {
                    "question": "What do you make of my fishing business?",
                    "response": self._businessDialogue,
                },
            ]
        )

    def _businessDialogue(self):
        """Old Tom's barroom banter about the player's fishing business,
        staged by boat tier."""
        if not self.player.hasBoat:
            return (
                "No boat yet? Can't rightly call yourself a fisherman around "
                "here without a crew behind you. Get one down at the docks!"
            )
        tier = business.currentTier(self.player)
        name = self.player.businessName or "your outfit"
        if tier == 1:
            return (
                "A little Rowboat crew, eh? Everybody's gotta start somewhere. "
                "Buy me a drink when you make your first real money!"
            )
        if tier == 2:
            return (
                "A Trawler! %s must be doing alright for itself. I might just "
                "have to start calling you 'boss' around here." % name
            )
        return (
            "A whole Fishing Fleet? %s is the toast of the village! Drinks "
            "are on you tonight, right?" % name
        )

    def run(self):
        li = ["Get drunk ( $10 )", "Gamble", "Talk to %s" % self.npc.name, "Go to Docks"]
        input = self.userInterface.showOptions(
            "You sit at the bar, watching the barkeep clean a mug with a dirty rag.", li
        )

        if input == "1":
            if self.player.canAfford(10):
                self.getDrunk()
                return LocationType.HOME
            else:
                self.currentPrompt.text = "You don't have enough money."
                return LocationType.TAVERN

        elif input == "2":
            self.currentPrompt.text = (
                "What will the dice land on? Current Bet: $%d" % self.currentBet
            )
            self.gamble()
            return LocationType.TAVERN

        elif input == "3":
            self.talkToNPC()
            return LocationType.TAVERN

        elif input == "4":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def getDrunk(self):
        self.userInterface.lotsOfSpace()
        self.userInterface.divider()

        self.player.spendMoney(10)

        for i in range(3):
            print("... ")
            sys.stdout.flush()
            time.sleep(1)

        self.stats.timesGottenDrunk += 1

        # A night of drinking is a gamble: you might lose money in a drunken
        # stupor, or you might overhear a lucrative rumor and come out ahead.
        roll = random.random()
        if roll < DRUNK_LOSS_CHANCE:
            if self.player.money > 0:
                # Lose between 10% and 50% of remaining money
                loss_percentage = random.uniform(0.1, 0.5)
                money_lost = int(self.player.money * loss_percentage)
                if money_lost > 0:
                    self.player.spendMoney(money_lost)
                    self.stats.moneyLostWhileDrunk += money_lost
                    self.currentPrompt.text = f"You have a headache. In your drunken stupor, you lost ${money_lost}!"
                else:
                    self.currentPrompt.text = "You have a headache."
            else:
                self.currentPrompt.text = "You have a headache."
        elif roll < DRUNK_LOSS_CHANCE + DRUNK_TIP_CHANCE:
            # Pick up a profitable rumor at the bar.
            tip = random.randint(15, 30)
            self.player.money += tip
            self.stats.totalMoneyMade += tip
            self.currentPrompt.text = (
                f"You have a headache, but a regular tipped you off to a hot catch — you earned ${tip}!"
            )
        else:
            self.currentPrompt.text = "You have a headache."

        self.timeService.increaseDay()

    def gamble(self):
        while True:
            li = ["1", "2", "3", "4", "5", "6", "Change Bet", "Back"]
            input = int(
                self.userInterface.showOptions(
                    "Once you place your bet, the burly man in front of you will throw the dice. "
                    "Guess the number right and he pays out %dx your bet."
                    % DICE_WIN_MULTIPLIER,
                    li,
                )
            )

            if 1 <= input <= 6 and self.currentBet > 0:
                self.diceThrow = random.randint(1, 6)

                if input == self.diceThrow:
                    winAmount = self.currentBet * DICE_WIN_MULTIPLIER
                    self.player.money += winAmount
                    self.stats.totalMoneyMade += winAmount
                    self.currentBet = 0
                    self.currentPrompt.text = (
                        "The dice rolled a %d! You won $%d! Care to try again? Current Bet: $%d"
                        % (self.diceThrow, winAmount, self.currentBet)
                    )
                    continue
                else:
                    self.player.spendMoney(self.currentBet)
                    self.stats.moneyLostFromGambling += self.currentBet
                    self.currentBet = 0
                    self.currentPrompt.text = (
                        "The dice rolled a %d! You lost your money! Care to try again? Current Bet: $%d"
                        % (self.diceThrow, self.currentBet)
                    )
                    continue
            elif input == 7:
                self.changeBet(
                    "How much money would you like to bet? Money: $%d"
                    % self.player.money
                )
                continue
            elif input == 8:
                self.currentPrompt.text = "What would you like to do?"
                break
            else:
                self.currentPrompt.text = "You didn't bet any money!"
                continue

    def changeBet(self, prompt):
        amount = self.userInterface.promptForNumber(prompt)
        if amount is None:
            self.currentPrompt.text = "Try again. Money: $%d" % self.player.money
            return
        self.amount = int(amount)

        if self.player.canAfford(self.amount):
            self.currentBet = self.amount

            self.currentPrompt.text = (
                "What will the dice land on? Current Bet: $%d" % self.currentBet
            )
            # Don't call self.gamble() recursively - let the main loop continue
        else:
            self.currentPrompt.text = (
                "You don't have that much money on you! Money: $%d" % self.player.money
            )

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
