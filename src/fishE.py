import os
import json
from location import bank, docks, home, shop, tavern
from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from player.playerJsonReaderWriter import PlayerJsonReaderWriter
from stats.statsJsonReaderWriter import StatsJsonReaderWriter
from world.timeServiceJsonReaderWriter import TimeServiceJsonReaderWriter
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterfaceFactory import UserInterfaceFactory
from ui.enum.uiType import UIType
from saveFileManager import SaveFileManager
from achievements import achievements
from housing import housing


# Total wealth (cash + bank) the player is working toward. Reaching it triggers
# a one-time victory message; the game then continues until the player retires.
GOAL_AMOUNT = 10000
GOAL_MILESTONE_NAME = "Reached Goal"

# Which front-end the game runs. Swap to UIType.PYGAME (or a future web type)
# here to change the interface — the rest of the game is front-end agnostic.
INTERFACE_TYPE = UIType.CONSOLE


# @author Daniel McCoy Stephenson
class FishE:
    def __init__(self, interfaceType=INTERFACE_TYPE):
        self.running = True

        self.playerJsonReaderWriter = PlayerJsonReaderWriter()
        self.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
        self.statsJsonReaderWriter = StatsJsonReaderWriter()
        self.saveFileManager = SaveFileManager()

        # Start from default (new-game) state, then build the UI so the save-file
        # manager can render and read input through the active front-end. A
        # chosen save is loaded over these defaults below.
        self.player = Player()
        self.stats = Stats()
        self.timeService = TimeService(self.player, self.stats)
        self.prompt = Prompt("What would you like to do?")
        self.userInterface = UserInterfaceFactory.create_user_interface(
            interfaceType, self.prompt, self.timeService, self.player
        )

        # Migrate old save files to new format if they exist
        self.saveFileManager.migrate_old_save_files()

        # Show save file selection menu (uses the UI above)
        self._selectSaveFile()

        # Load the chosen slot over the defaults if it has data
        player_path = self.saveFileManager.get_save_path("player.json")
        if os.path.exists(player_path) and os.path.getsize(player_path) > 0:
            self.loadPlayer()

        stats_path = self.saveFileManager.get_save_path("stats.json")
        if os.path.exists(stats_path) and os.path.getsize(stats_path) > 0:
            self.loadStats()

        time_path = self.saveFileManager.get_save_path("timeService.json")
        if os.path.exists(time_path) and os.path.getsize(time_path) > 0:
            self.loadTimeService()

        # Point the UI at the (possibly reloaded) game state.
        self.userInterface.player = self.player
        self.userInterface.timeService = self.timeService

        self.locations = {
            LocationType.BANK: bank.Bank(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.DOCKS: docks.Docks(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.HOME: home.Home(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.SHOP: shop.Shop(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
            LocationType.TAVERN: tavern.Tavern(
                self.userInterface,
                self.prompt,
                self.player,
                self.stats,
                self.timeService,
            ),
        }

        self.currentLocation = LocationType.HOME

    def _selectSaveFile(self):
        """Display the save-file menu through the UI and let the player choose.

        Slots and actions are presented as numbered options (so the menu renders
        and reads input through the active front-end — console or pygame)."""
        while True:  # loop instead of recursion to avoid stack overflow
            save_files = self.saveFileManager.list_save_files()

            # Build the option list, tracking what each option does in parallel.
            options = []
            actions = []  # (kind, arg) for the option at the same index
            for save in save_files:
                metadata = save["metadata"]
                options.append(
                    "Load Slot %d (Day %d, $%d, %d fish)"
                    % (
                        save["slot"],
                        metadata.get("day", 1),
                        metadata.get("money", 0),
                        metadata.get("fishCount", 0),
                    )
                )
                actions.append(("load", save["slot"]))

            next_slot = self.saveFileManager.get_next_available_slot()
            if next_slot is not None:
                options.append("Create New Save (Slot %d)" % next_slot)
                actions.append(("new", next_slot))
            if save_files:
                options.append("Delete a Save File")
                actions.append(("delete", None))
            options.append("Quit")
            actions.append(("quit", None))

            choice = int(
                self.userInterface.showOptions("FishE - Save File Manager", options)
            )
            kind, arg = actions[choice - 1]

            if kind == "load" or kind == "new":
                self.saveFileManager.select_save_slot(arg)
                return
            elif kind == "delete":
                self._deleteSaveFile(save_files)
                # loop to show the refreshed menu either way
            elif kind == "quit":
                exit(0)

    def _deleteSaveFile(self, save_files):
        """Delete a save file. Returns True if a file was deleted, False if cancelled."""
        options = ["Delete Slot %d" % save["slot"] for save in save_files]
        options.append("Cancel")

        choice = int(self.userInterface.showOptions("Delete a Save File", options))
        if choice == len(options):  # Cancel
            return False

        slot_num = save_files[choice - 1]["slot"]
        confirm = int(
            self.userInterface.showOptions(
                "Permanently delete Slot %d?" % slot_num,
                ["Yes, delete it", "No, keep it"],
            )
        )
        if confirm != 1:
            return False

        if self.saveFileManager.delete_save_slot(slot_num):
            self.userInterface.showDialogue("Slot %d deleted." % slot_num)
            return True

        self.userInterface.showDialogue("Failed to delete Slot %d." % slot_num)
        return False

    def play(self):
        while self.running:
            # show the current location and goal progress in the UI header
            self.userInterface.currentLocationName = self.currentLocation.capitalize()
            self.userInterface.goalProgress = "$%d / $%d" % (
                self.getTotalWealth(),
                GOAL_AMOUNT,
            )

            # change location
            nextLocation = self.locations[self.currentLocation].run()

            if nextLocation == LocationType.NONE:
                self.running = False

            self.currentLocation = nextLocation

            # announce any milestones just crossed (appended so the action's own
            # message is preserved on the next screen)
            newlyEarned = achievements.getNewlyEarned(self.stats)
            for milestone in newlyEarned:
                self.prompt.text += "  [Milestone unlocked: %s!]" % milestone["name"]

            # announce reaching the wealth goal once (the run continues)
            self.announceGoalIfReached()

            # increase time - almost any action can roll a day over, so this
            # is the one place guaranteed to catch an eviction regardless of
            # what triggered it (appended so the action's own message is
            # preserved on the next screen, same as milestones above)
            if self.timeService.increaseTime()["evicted"]:
                self.prompt.text += "  " + housing.EVICTION_MESSAGE

            self.save()

    def getTotalWealth(self):
        return self.player.money + self.player.moneyInBank

    def announceGoalIfReached(self):
        """Announce the wealth goal the first time it is reached.

        The persisted earnedMilestones list doubles as the "already announced"
        flag, so the victory is shown once and not repeated on later actions or
        after a reload. Returns True only on the announcing call."""
        if (
            self.getTotalWealth() >= GOAL_AMOUNT
            and GOAL_MILESTONE_NAME not in self.stats.earnedMilestones
        ):
            self.stats.earnedMilestones.append(GOAL_MILESTONE_NAME)
            self.prompt.text += (
                "  [GOAL REACHED! You've built your fortune of $%d! "
                "Keep fishing, or retire from the Home menu.]" % GOAL_AMOUNT
            )
            return True
        return False

    def save(self):
        # create data directory - use SaveFileManager's directory
        if not os.path.exists(self.saveFileManager.data_directory):
            os.makedirs(self.saveFileManager.data_directory, exist_ok=True)

        try:
            with open(
                self.saveFileManager.get_save_path("player.json"), "w"
            ) as playerSaveFile:
                self.playerJsonReaderWriter.writePlayerToFile(
                    self.player, playerSaveFile
                )

            with open(
                self.saveFileManager.get_save_path("timeService.json"), "w"
            ) as timeServiceSaveFile:
                self.timeServiceJsonReaderWriter.writeTimeServiceToFile(
                    self.timeService, timeServiceSaveFile
                )

            with open(
                self.saveFileManager.get_save_path("stats.json"), "w"
            ) as statsSaveFile:
                self.statsJsonReaderWriter.writeStatsToFile(self.stats, statsSaveFile)
        except (IOError, OSError) as e:
            print(f"\n Warning: Failed to save game: {e}")
            # Game continues even if save fails

    def loadPlayer(self):
        try:
            with open(
                self.saveFileManager.get_save_path("player.json"), "r"
            ) as playerSaveFile:
                self.player = self.playerJsonReaderWriter.readPlayerFromFile(
                    playerSaveFile
                )
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load player data: {e}")
            print(" Creating new player...")
            self.player = Player()

    def loadStats(self):
        try:
            with open(
                self.saveFileManager.get_save_path("stats.json"), "r"
            ) as statsSaveFile:
                self.stats = self.statsJsonReaderWriter.readStatsFromFile(statsSaveFile)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load stats data: {e}")
            print(" Creating new stats...")
            self.stats = Stats()

    def loadTimeService(self):
        try:
            with open(
                self.saveFileManager.get_save_path("timeService.json"), "r"
            ) as timeServiceSaveFile:
                self.timeService = (
                    self.timeServiceJsonReaderWriter.readTimeServiceFromFile(
                        timeServiceSaveFile, self.player, self.stats
                    )
                )
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load time service data: {e}")
            print(" Creating new time service...")
            self.timeService = TimeService(self.player, self.stats)


if __name__ == "__main__":
    game = FishE()
    game.play()
