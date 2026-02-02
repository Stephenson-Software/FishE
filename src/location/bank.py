from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC


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
        self.npc = NPC(
            "Margaret the Teller",
            "I've worked at this bank for fifteen years and I take pride in keeping everyone's money safe. "
            "My grandmother taught me the value of saving, and I've helped many fishermen in this village "
            "secure their futures. A penny saved is a penny earned, as they say!",
            [
                {
                    "question": "How does the bank work?",
                    "response": "The bank is simple and safe! You can deposit money when you have some on hand, "
                               "and withdraw it whenever you need. We keep your money secure - "
                               "no risk of losing it to gambling or spending it accidentally! "
                               "Plus, your savings earn interest over time. The more you save, the more you earn. "
                               "It's the smart way to grow your wealth!"
                },
                {
                    "question": "Tell me about interest rates.",
                    "response": "Ah yes, interest! Every day that passes, your savings grow by a small percentage. "
                               "It might not seem like much at first, but over time it really adds up! "
                               "The interest is automatically added to your bank account. "
                               "Think of it as the bank paying you for keeping your money with us. "
                               "The more you save, the more interest you earn!"
                },
                {
                    "question": "Should I save or spend my money?",
                    "response": "That's the eternal question, isn't it? Here's my advice: "
                               "Keep some money on hand for daily needs - buying bait, paying for drinks, gambling if you must. "
                               "But save the rest in the bank! Your savings will grow with interest, "
                               "and you'll have a nice cushion for the future. "
                               "Many fishermen spend everything they earn and have nothing to show for it. "
                               "Be smarter than that!"
                },
                {
                    "question": "What's the most important financial advice?",
                    "response": "Save regularly, even if it's just a little bit. Every coin counts! "
                               "Don't gamble away your hard-earned money - the odds are rarely in your favor. "
                               "Invest in good bait to improve your catches, but save the profits. "
                               "And remember: it's not about how much you earn, it's about how much you keep. "
                               "That's the secret to real wealth!"
                }
            ]
        )

    def run(self):
        li = ["Make a Deposit", "Make a Withdrawal", "Talk to %s" % self.npc.name, "Go to docks"]
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
            self.talkToNPC()
            return LocationType.BANK

        elif input == "4":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def deposit(self):
        while True:
            self.userInterface.lotsOfSpace()
            self.userInterface.divider()
            print(self.currentPrompt.text)
            self.userInterface.divider()

            try:
                amount = float(input("> "))
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
            self.userInterface.lotsOfSpace()
            self.userInterface.divider()
            print(self.currentPrompt.text)
            self.userInterface.divider()

            try:
                amount = float(input("> "))
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

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
