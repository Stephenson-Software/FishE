# @author Daniel McCoy Stephenson
"""FishE's user-interface contract, now tak's (tak.ui.BaseUserInterface).

The kit's contract knows nothing about days, money or fish: a front-end
takes a *header provider* and draws whatever chips it returns. This class is
FishE's adapter - it keeps the (currentPrompt, timeService, player)
constructor every FishE front-end and test uses, and builds the header the
village has always shown from those two objects. The header fields the game
loop sets before each render (currentLocationName, goalProgress) live here
too, as before.
"""

from tak import formatHour
from tak.ui import BaseUserInterface as KitBaseUserInterface
from tak.ui.base import (
    unavailableMessage,
    unavailableSuffix,
)  # noqa: F401 - re-exported

from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService
from housing import housing

# Below this the player is too tired to fish; the browser header flags it.
LOW_ENERGY = 10


class BaseUserInterface(KitBaseUserInterface):
    def __init__(
        self, currentPrompt: Prompt, timeService: TimeService, player: Player, **kwargs
    ):
        # kwargs travel on to the next kit class in the MRO: the web front-end
        # takes its title, address and server switches through here.
        super().__init__(currentPrompt, header=self._buildHeader, **kwargs)
        self.timeService = timeService
        self.player = player

        self.prompt = "Make your choice!"
        # Header fields the game loop sets before each render; empty hides the line.
        self.currentLocationName = ""
        self.goalProgress = ""

        # Kept for the pygame front-end and anything else that indexed it.
        self.times = {hour: formatHour(hour) for hour in range(24)}

    def _buildHeader(self):
        """The status line, as chips. Text matches what the console has always
        printed; the classes are what the browser styles."""
        chips = ["Day %d" % self.timeService.day]
        if self.currentLocationName:
            chips.append("Location: " + self.currentLocationName)
        chips.append(self.times[self.timeService.time])
        chips.append("Money: $%.2f" % self.player.money)
        chips.append("Fish: %d" % self.player.fishCount)
        energy = "Energy: %d/%d" % (self.player.energy, housing.maxEnergy(self.player))
        chips.append(
            {"text": energy, "class": "low"}
            if self.player.energy < LOW_ENERGY
            else energy
        )
        if self.player.operatorMode:
            chips.append({"text": "[OPERATOR MODE]", "class": "operator"})
        if self.goalProgress:
            chips.append("Goal: " + self.goalProgress)
        return {
            "title": "FishE - Day %d, $%.2f"
            % (self.timeService.day, self.player.money),
            "chips": chips,
        }
