import os
import json
import shutil
from datetime import datetime
from jsonschema.exceptions import ValidationError
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
from browserSaveSync import syncBrowserSaves
from achievements import achievements
from achievements.achievements import GOAL_AMOUNT, GOAL_MILESTONE_NAME
from housing import housing
from progression import progression
from config.config import Config

# Which front-end the game runs. Swap to UIType.PYGAME (or a future web type)
# here to change the interface — the rest of the game is front-end agnostic.
INTERFACE_TYPE = UIType.CONSOLE


# @author Daniel McCoy Stephenson
class FishE:
    def __init__(self, interfaceType=INTERFACE_TYPE):
        self.running = True

        self.config = Config()
        self.playerJsonReaderWriter = PlayerJsonReaderWriter()
        self.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
        self.statsJsonReaderWriter = StatsJsonReaderWriter()
        self.saveFileManager = SaveFileManager(data_directory=self.config.dataDirectory)

        # What the load block below could not read, one description per file.
        # Collected rather than reported one file at a time so a slot with
        # three bad files costs the player one dialogue instead of three.
        self.failedLoads = []

        # Start from default (new-game) state, then build the UI so the save-file
        # manager can render and read input through the active front-end. A
        # chosen save is loaded over these defaults below.
        self.player = Player(self.config)
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

        # A failed load leaves fresh objects in place of the player's run, and
        # save() writes them back after the very next action - so the bytes
        # that failed have to be copied aside before play() is ever reached.
        if self.failedLoads:
            self._preserveDamagedSave()

        # loadPlayer()/loadStats() rebind self.player/self.stats to brand-new
        # objects, but only loadTimeService() rebuilds the TimeService around
        # them. When a slot has player.json/stats.json but no timeService.json,
        # the TimeService built from the defaults above would keep pointing at
        # the discarded objects, so every daily tick (interest, crew catch,
        # investment income, rent) would apply to a player nobody reads.
        self.timeService.player = self.player
        self.timeService.stats = self.stats

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

        # A loaded save may predate the progression module entirely, or may
        # have earned unlocks between the last save and now; grant those
        # quietly so the village is never re-locked around an established
        # player (see progression.catchUp).
        progression.catchUp(self.player, self.stats)

        # The game opens on the docks, with fishing as the only thing on the
        # menu. Everywhere else in the village is revealed as it is earned -
        # see src/progression.
        self.currentLocation = LocationType.DOCKS
        if progression.isFreshStart(self.stats):
            self.prompt.text = progression.OPENING_PROMPT

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
            # The fortune the run is ultimately about is itself a late reveal:
            # a player on their first cast is working toward filling a bucket,
            # not toward $10,000, and an empty string hides the line.
            if progression.isUnlocked(self.stats, progression.GOAL):
                self.userInterface.goalProgress = "$%d / $%d" % (
                    self.getTotalWealth(),
                    GOAL_AMOUNT,
                )
            else:
                self.userInterface.goalProgress = ""

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

            # announce the one thing the player has just opened up, with the
            # reason they opened it, so the newly-appeared menu entry is
            # explained on the same screen it first shows up on (appended for
            # the same reason as milestones above)
            unlock = progression.getNextUnlock(self.player, self.stats)
            if unlock is not None:
                self.prompt.text += "  [%s]" % unlock["announcement"]

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

    def _describeLoadFailure(self, filename, error):
        """One short line naming a save file and why it would not load.

        Kept to a single trimmed line because this ends up inside a dialogue
        box: jsonschema's ValidationError renders as a multi-paragraph dump of
        the whole instance and schema, which no front-end can show and no
        player would read. Its .message is the one-line reason; every other
        error the load handlers catch is already short."""
        reason = getattr(error, "message", None) or str(error)
        lines = reason.splitlines()
        reason = lines[0] if lines else error.__class__.__name__
        if len(reason) > 120:
            reason = reason[:117] + "..."
        return "%s (%s)" % (filename, reason)

    def _preserveDamagedSave(self):
        """Copy a slot that would not load aside, and tell the player about it.

        The load handlers fall back to fresh objects, and save() runs at the
        end of every loop iteration, so without this the player's first action
        writes a brand-new character over the run that failed to load - bytes
        that were recoverable by hand until that moment.

        The whole slot is copied, not only the file that failed: restoring a
        run needs player.json, stats.json and timeService.json together, so
        keeping just the unreadable one would preserve nothing usable.

        Returns the backup directory, or None if nothing could be copied."""
        slotDirectory = os.path.dirname(
            self.saveFileManager.get_save_path("player.json")
        )
        backupDirectory = os.path.join(
            slotDirectory, "damaged-%s" % datetime.now().strftime("%Y%m%d-%H%M%S")
        )

        copied = []
        try:
            os.makedirs(backupDirectory, exist_ok=True)
            for name in sorted(os.listdir(slotDirectory)):
                source = os.path.join(slotDirectory, name)
                if os.path.isfile(source):
                    shutil.copy2(source, os.path.join(backupDirectory, name))
                    copied.append(name)
        except (IOError, OSError):
            copied = []

        if not copied:
            # An empty or half-written backup is worse than none: it looks like
            # a rescued save and would be trusted as one.
            shutil.rmtree(backupDirectory, ignore_errors=True)
            backupDirectory = None

        if backupDirectory is not None:
            # Same reason delete_save_slot flushes: under the browser front-end
            # the copy exists only in the Worker's in-memory filesystem until
            # it is mirrored to IndexedDB.
            syncBrowserSaves()
            whereItWent = (
                "A copy of the slot as it was has been kept in:\n  %s\n\n"
                % backupDirectory
            )
        else:
            whereItWent = (
                "The slot could not be copied aside, so it will be overwritten "
                "as you play. Close the game now if you want to keep it.\n\n"
            )

        self.userInterface.showDialogue(
            "This save could not be read, so a new game has been started in "
            "its slot.\n\nWhat failed to load:\n  %s\n\n%sNothing you did "
            "caused this - a save can be damaged by a crash or a power cut "
            "while the game is writing to disk."
            % ("\n  ".join(self.failedLoads), whereItWent)
        )
        return backupDirectory

    def _writeSaveFile(self, filename, writeContents):
        """Write one save file so a failure can never truncate the old one.

        Opening the real path with mode "w" empties it before a single byte is
        written, so a crash, a full disk or a kill mid-dump leaves a partial
        file and no intact copy anywhere - which is how a slot becomes
        unreadable in the first place. The contents go to a temporary file
        beside the target instead, and os.replace() (atomic on POSIX and
        Windows) swaps it in only once it is complete."""
        path = self.saveFileManager.get_save_path(filename)
        temporaryPath = path + ".tmp"
        try:
            with open(temporaryPath, "w") as saveFile:
                writeContents(saveFile)
            os.replace(temporaryPath, path)
        except (IOError, OSError):
            # A half-written temporary file is worth nothing and would only
            # confuse a later recovery, so it goes; the previous save stays.
            try:
                os.remove(temporaryPath)
            except OSError:
                pass
            raise

    def save(self):
        # create data directory - use SaveFileManager's directory
        if not os.path.exists(self.saveFileManager.data_directory):
            os.makedirs(self.saveFileManager.data_directory, exist_ok=True)

        try:
            self._writeSaveFile(
                "player.json",
                lambda saveFile: self.playerJsonReaderWriter.writePlayerToFile(
                    self.player, saveFile
                ),
            )
            self._writeSaveFile(
                "timeService.json",
                lambda saveFile: self.timeServiceJsonReaderWriter.writeTimeServiceToFile(
                    self.timeService, saveFile
                ),
            )
            self._writeSaveFile(
                "stats.json",
                lambda saveFile: self.statsJsonReaderWriter.writeStatsToFile(
                    self.stats, saveFile
                ),
            )
        except (IOError, OSError) as e:
            # Said through the front-end rather than printed: stdout is not
            # rendered at all by pygame or either web front-end, and the
            # console clears it on the next screen. Repeated on every action
            # that fails to save, because a run that is no longer being
            # written down is exactly what the player must not miss.
            self.userInterface.showDialogue(
                "Your game could not be saved: %s\n\n"
                "The run continues, but progress since the last successful "
                "save is not on disk. Check for a full or read-only disk." % e
            )
            # Game continues even if save fails
            return

        # Under the Pyodide front-end the writes above landed in the Worker's
        # in-memory filesystem; this is what actually gets them into the
        # browser's IndexedDB. A no-op for every other front-end.
        syncBrowserSaves()

    def loadPlayer(self):
        try:
            with open(
                self.saveFileManager.get_save_path("player.json"), "r"
            ) as playerSaveFile:
                self.player = self.playerJsonReaderWriter.readPlayerFromFile(
                    playerSaveFile
                )
        except (IOError, OSError, json.JSONDecodeError, ValidationError) as e:
            self.failedLoads.append(self._describeLoadFailure("player.json", e))
            self.player = Player(self.config)

    def loadStats(self):
        try:
            with open(
                self.saveFileManager.get_save_path("stats.json"), "r"
            ) as statsSaveFile:
                self.stats = self.statsJsonReaderWriter.readStatsFromFile(statsSaveFile)
        except (IOError, OSError, json.JSONDecodeError, ValidationError) as e:
            self.failedLoads.append(self._describeLoadFailure("stats.json", e))
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
        except (IOError, OSError, json.JSONDecodeError, ValidationError) as e:
            self.failedLoads.append(self._describeLoadFailure("timeService.json", e))
            self.timeService = TimeService(self.player, self.stats)


if __name__ == "__main__":
    game = FishE()
    game.play()
