import random
import sys
import time

from location.enum.locationType import LocationType

from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface


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

    def run(self):
        li = ["Get drunk ( $10 )", "Gamble", "Go to Docks"]
        input = self.userInterface.showOptions(
            "You sit at the bar, watching the barkeep clean a mug with a dirty rag.", li
        )

        if input == "1":
            if self.player.money >= 10:
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
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def getDrunk(self):
        self.userInterface.lotsOfSpace()
        self.userInterface.divider()

        self.player.money -= 10

        for i in range(3):
            print("... ")
            sys.stdout.flush()
            time.sleep(1)

        self.stats.timesGottenDrunk += 1

        self.timeService.increaseDay()
        self.currentPrompt.text = "You have a headache."

    def gamble(self):
        while True:
            li = ["1", "2", "3", "4", "5", "6", "Change Bet", "Back"]
            input = int(
                self.userInterface.showOptions(
                    "Once you place your bet, the burly man in front of you will throw the dice.",
                    li,
                )
            )

            if 1 <= input <= 6 and self.currentBet > 0:
                self.diceThrow = random.randint(1, 6)

                if input == self.diceThrow:
                    winAmount = self.currentBet
                    self.player.money += self.currentBet
                    self.stats.totalMoneyMade += self.currentBet
                    self.currentBet = 0
                    self.currentPrompt.text = (
                        "The dice rolled a %d! You won $%d! Care to try again? Current Bet: $%d"
                        % (self.diceThrow, winAmount, self.currentBet)
                    )
                    continue
                else:
                    self.player.money -= self.currentBet
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
        try:
            userInput = self.userInterface.getInput(prompt)
            self.amount = int(userInput)
        except ValueError:
            self.currentPrompt.text = "Try again. Money: $%d" % self.player.money
            return

        if self.amount <= self.player.money:
            self.currentBet = self.amount

            self.currentPrompt.text = (
                "What will the dice land on? Current Bet: $%d" % self.currentBet
            )
            # Don't call self.gamble() recursively - let the main loop continue
        else:
            self.currentPrompt.text = (
                "You don't have that much money on you! Money: $%d" % self.player.money
            )
