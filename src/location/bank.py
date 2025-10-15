from pstats import Stats
from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from ui.userInterface import UserInterface


# @author Daniel McCoy Stephenson
class Bank:
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

    def run(self):
        li = ["Make a Deposit", "Make a Withdrawal", "Go to docks"]
        input = self.userInterface.showOptions(
            "You're at the front of the line and the teller asks you what you want to do.",
            li,
        )

        if input == "1":
            if self.player.money > 0:
                self.currentPrompt.text = (
                    "How much would you like to deposit? Money: $%.2f"
                    % self.player.money
                )
                self.deposit()
            else:
                self.currentPrompt.text = "You don't have any money on you!"
            return LocationType.BANK

        elif input == "2":
            if self.player.moneyInBank > 0:
                self.currentPrompt.text = (
                    "How much would you like to withdraw? Money In Bank: $%.2f"
                    % self.player.moneyInBank
                )
                self.withdraw()
            else:
                self.currentPrompt.text = "You don't have any money in the bank!"
            return LocationType.BANK

        elif input == "3":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def deposit(self):
        while True:
            try:
                userInput = self.userInterface.getInput(self.currentPrompt.text)
                amount = float(userInput)
            except ValueError:
                self.currentPrompt.text = "Try again. Money: $%.2f" % self.player.money
                continue

            if amount <= self.player.money:
                self.player.moneyInBank += amount
                self.player.money -= amount

                self.currentPrompt.text = "$%.2f deposited successfully." % amount
            else:
                self.currentPrompt.text = "You don't have that much money on you!"
            break

    def withdraw(self):
        while True:
            try:
                userInput = self.userInterface.getInput(self.currentPrompt.text)
                amount = float(userInput)
            except ValueError:
                self.currentPrompt.text = (
                    "Try again. Money In Bank: $%.2f" % self.player.moneyInBank
                )
                continue

            if amount <= self.player.moneyInBank:
                self.player.money += amount
                self.player.moneyInBank -= amount

                self.currentPrompt.text = "$%.2f withdrawn successfully." % amount
            else:
                self.currentPrompt.text = "You don't have that much money in the bank!"
            break
