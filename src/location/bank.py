from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC
from business import business
from investments import investments


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
                    "question": "Tell me about yourself.",
                    "response": "I've worked at this bank for fifteen years and I take pride in keeping everyone's money safe. "
                    "My grandmother taught me the value of saving, and I've helped many fishermen in this village "
                    "secure their futures. A penny saved is a penny earned, as they say!",
                },
                {
                    "question": "How does the bank work?",
                    "response": "The bank is simple and safe! You can deposit money when you have some on hand, "
                    "and withdraw it whenever you need. We keep your money secure - "
                    "no risk of losing it to gambling or spending it accidentally! "
                    "Plus, your savings earn interest over time. The more you save, the more you earn. "
                    "It's the smart way to grow your wealth!",
                },
                {
                    "question": "Tell me about interest rates.",
                    "response": "Ah yes, interest! Every day that passes, your savings grow by a small percentage. "
                    "It might not seem like much at first, but over time it really adds up! "
                    "The interest is automatically added to your bank account. "
                    "Think of it as the bank paying you for keeping your money with us. "
                    "The more you save, the more interest you earn!",
                },
                {
                    "question": "Should I save or spend my money?",
                    "response": "That's the eternal question, isn't it? Here's my advice: "
                    "Keep some money on hand for daily needs - buying bait, paying for drinks, gambling if you must. "
                    "But save the rest in the bank! Your savings will grow with interest, "
                    "and you'll have a nice cushion for the future. "
                    "Many fishermen spend everything they earn and have nothing to show for it. "
                    "Be smarter than that!",
                },
                {
                    "question": "What's the most important financial advice?",
                    "response": "Save regularly, even if it's just a little bit. Every coin counts! "
                    "Don't gamble away your hard-earned money - the odds are rarely in your favor. "
                    "Invest in good bait to improve your catches, but save the profits. "
                    "And remember: it's not about how much you earn, it's about how much you keep. "
                    "That's the secret to real wealth!",
                },
                {
                    "question": "What do you think of my fishing business?",
                    "response": self._businessDialogue,
                },
            ],
        )

    def _businessDialogue(self):
        """Margaret's savings-minded take on the player's fishing business,
        staged by boat ownership/crew size."""
        if not self.player.hasBoat:
            return (
                "A boat's a fine goal to save toward! Set some money aside "
                "here and it'll be waiting for you when you're ready to buy one."
            )
        if self.player.workers == 0:
            return (
                "A boat with no crew is just a rowboat and a dream! Bank your "
                "catch money for a while and you'll have their wages covered "
                "in no time."
            )
        if business.currentTier(self.player) >= 3:
            return (
                "A whole Fishing Fleet, paying out $%d in wages so far? "
                "You could retire a wealthy soul if you keep banking those "
                "profits!" % self.stats.totalWagesPaid
            )
        return (
            "Your crew's brought in $%d in wages paid out so far - quite the "
            "little enterprise! Don't let it all burn a hole in your pocket, "
            "park some of it here and let it earn interest." % self.stats.totalWagesPaid
        )

    def run(self):
        li = [
            "Make a Deposit",
            "Make a Withdrawal",
            "Talk to %s" % self.npc.name,
            "Manage Investment Properties",
            "Go to docks",
        ]
        input = self.userInterface.showOptions(
            "You're at the front of the line and the teller asks you what you want to do.",
            li,
        )

        if input == "1":
            if self.player.operatorMode or self.player.money > 0:
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
            self.manageInvestments()
            return LocationType.BANK

        elif input == "5":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS

    def _investmentsStatus(self):
        lines = ["Investment Properties:"]
        owned = investments.ownedCounts(self.player)
        if not owned:
            lines.append("You don't own any yet - they pay rental income daily.")
        else:
            for typeId in range(1, len(investments.PROPERTY_TYPES) + 1):
                count = owned.get(typeId, 0)
                if count:
                    info = investments.typeInfo(typeId)
                    lines.append(
                        "%s x%d - $%d/day each"
                        % (info["name"], count, info["dailyIncome"])
                    )
        return "\n".join(lines)

    def manageInvestments(self):
        while True:
            options = []
            actions = []
            owned = investments.ownedCounts(self.player)
            for typeId in range(1, len(investments.PROPERTY_TYPES) + 1):
                info = investments.typeInfo(typeId)
                options.append(
                    "Buy a %s ($%d, earns $%d/day)"
                    % (info["name"], info["cost"], info["dailyIncome"])
                )
                actions.append(("buy", typeId))
                if owned.get(typeId, 0) > 0:
                    options.append(
                        "Sell a %s (+$%d)" % (info["name"], info["resaleValue"])
                    )
                    actions.append(("sell", typeId))
            options.append("Back")
            actions.append(("back", None))

            choice = int(
                self.userInterface.showOptions(self._investmentsStatus(), options)
            )
            action, typeId = actions[choice - 1]

            if action == "buy":
                if investments.buyProperty(self.player, typeId, self.stats):
                    self.currentPrompt.text = (
                        "You bought a %s!" % investments.typeInfo(typeId)["name"]
                    )
                else:
                    self.currentPrompt.text = "You can't afford that property yet."
            elif action == "sell":
                investments.sellProperty(self.player, typeId)
                self.currentPrompt.text = (
                    "You sold a %s." % investments.typeInfo(typeId)["name"]
                )
            elif action == "back":
                self.currentPrompt.text = "What would you like to do?"
                return

    def deposit(self):
        while True:
            amount = self.userInterface.promptForNumber(self.currentPrompt.text)
            if amount is None:
                self.currentPrompt.text = "Try again. Money: $%.2f" % self.player.money
                continue

            if self.player.canAfford(amount):
                self.player.moneyInBank += amount
                self.player.spendMoney(amount)

                self.currentPrompt.text = "$%.2f deposited successfully." % amount
            else:
                self.currentPrompt.text = "You don't have that much money on you!"
            break

    def withdraw(self):
        while True:
            amount = self.userInterface.promptForNumber(self.currentPrompt.text)
            if amount is None:
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
