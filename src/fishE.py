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
from ui.userInterface import UserInterface
from saveFileManager import SaveFileManager
from achievements import achievements


# @author Daniel McCoy Stephenson
class FishE:
    def __init__(self):
        self.running = True

        self.playerJsonReaderWriter = PlayerJsonReaderWriter()
        self.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
        self.statsJsonReaderWriter = StatsJsonReaderWriter()
        self.saveFileManager = SaveFileManager()

        # Migrate old save files to new format if they exist
        self.saveFileManager.migrate_old_save_files()

        # Show save file selection menu
        self._selectSaveFile()

        # if save file exists, load it
        player_path = self.saveFileManager.get_save_path("player.json")
        if os.path.exists(player_path) and os.path.getsize(player_path) > 0:
            self.loadPlayer()
        else:
            self.player = Player()

        # if save file exists, load it
        stats_path = self.saveFileManager.get_save_path("stats.json")
        if os.path.exists(stats_path) and os.path.getsize(stats_path) > 0:
            self.loadStats()
        else:
            self.stats = Stats()

        # if save file exists, load it
        time_path = self.saveFileManager.get_save_path("timeService.json")
        if os.path.exists(time_path) and os.path.getsize(time_path) > 0:
            self.loadTimeService()
        else:
            self.timeService = TimeService(self.player, self.stats)

        self.prompt = Prompt("What would you like to do?")

        self.userInterface = UserInterface(self.prompt, self.timeService, self.player)

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
        """Display save file selection menu and let user choose"""
        while True:  # Use loop instead of recursion to avoid stack overflow
            save_files = self.saveFileManager.list_save_files()

            print("\n" * 20)
            print("-" * 75)
            print("\n FISHE - SAVE FILE MANAGER")
            print("-" * 75)

            if save_files:
                print("\n Available Save Files:\n")
                for save in save_files:
                    metadata = save["metadata"]
                    print(f" [{save['slot']}] Save Slot {save['slot']}")
                    print(f"     Day: {metadata.get('day', 1)}")
                    print(f"     Money: ${metadata.get('money', 0)}")
                    print(f"     Fish: {metadata.get('fishCount', 0)}")
                    print(f"     Last Modified: {metadata.get('last_modified', 'Unknown')}")
                    print()

            next_slot = self.saveFileManager.get_next_available_slot()
            if next_slot is not None:
                print(f" [N] Create New Save (Slot {next_slot})")
            if save_files:
                print(" [D] Delete a Save File")
            print(" [Q] Quit")
            print("-" * 75)

            choice = input("\n Select an option: ").strip().upper()

            if choice == "Q":
                print("\n Goodbye!")
                exit(0)
            elif choice == "N" and next_slot is not None:
                self.saveFileManager.select_save_slot(next_slot)
                print(f"\n Creating new save in Slot {next_slot}...")
                return
            elif choice == "N" and next_slot is None:
                print(" All save slots are full. Please delete a save first.")
            elif choice == "D" and save_files:
                if self._deleteSaveFile(save_files):
                    # Continue loop to show updated menu
                    continue
                else:
                    # User cancelled, continue loop
                    continue
            elif choice.isdigit():
                slot_num = int(choice)
                if any(save["slot"] == slot_num for save in save_files):
                    self.saveFileManager.select_save_slot(slot_num)
                    print(f"\n Loading Save Slot {slot_num}...")
                    return
                else:
                    print(" Invalid slot number. Try again.")
            else:
                print(" Invalid choice. Try again.")

    def _deleteSaveFile(self, save_files):
        """Delete a save file. Returns True if a file was deleted, False if cancelled."""
        print("\n" * 20)
        print("-" * 75)
        print("\n DELETE SAVE FILE")
        print("-" * 75)
        print("\n Which save file would you like to delete?\n")

        for save in save_files:
            print(f" [{save['slot']}] Save Slot {save['slot']}")

        print(" [C] Cancel")
        print("-" * 75)

        while True:
            choice = input("\n Select a slot to delete: ").strip().upper()

            if choice == "C":
                return False
            elif choice.isdigit():
                slot_num = int(choice)
                if any(save["slot"] == slot_num for save in save_files):
                    confirm = input(f"\n Are you sure you want to delete Slot {slot_num}? (Y/N): ").strip().upper()
                    if confirm == "Y":
                        if self.saveFileManager.delete_save_slot(slot_num):
                            print(f"\n Slot {slot_num} deleted successfully.")
                            input("\n [ CONTINUE ]")
                            return True
                        else:
                            print(f"\n Failed to delete Slot {slot_num}.")
                            return False
                    else:
                        return False
                else:
                    print(" Invalid slot number. Try again.")
            else:
                print(" Invalid choice. Try again.")

    def play(self):
        while self.running:
            # show the current location in the UI header
            self.userInterface.currentLocationName = self.currentLocation.capitalize()

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

            # increase time & save
            self.timeService.increaseTime()
            self.save()

    def save(self):
        # create data directory - use SaveFileManager's directory
        if not os.path.exists(self.saveFileManager.data_directory):
            os.makedirs(self.saveFileManager.data_directory, exist_ok=True)

        try:
            with open(self.saveFileManager.get_save_path("player.json"), "w") as playerSaveFile:
                self.playerJsonReaderWriter.writePlayerToFile(self.player, playerSaveFile)

            with open(self.saveFileManager.get_save_path("timeService.json"), "w") as timeServiceSaveFile:
                self.timeServiceJsonReaderWriter.writeTimeServiceToFile(
                    self.timeService, timeServiceSaveFile
                )

            with open(self.saveFileManager.get_save_path("stats.json"), "w") as statsSaveFile:
                self.statsJsonReaderWriter.writeStatsToFile(self.stats, statsSaveFile)
        except (IOError, OSError) as e:
            print(f"\n Warning: Failed to save game: {e}")
            # Game continues even if save fails

    def loadPlayer(self):
        try:
            with open(self.saveFileManager.get_save_path("player.json"), "r") as playerSaveFile:
                self.player = self.playerJsonReaderWriter.readPlayerFromFile(playerSaveFile)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load player data: {e}")
            print(" Creating new player...")
            self.player = Player()

    def loadStats(self):
        try:
            with open(self.saveFileManager.get_save_path("stats.json"), "r") as statsSaveFile:
                self.stats = self.statsJsonReaderWriter.readStatsFromFile(statsSaveFile)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load stats data: {e}")
            print(" Creating new stats...")
            self.stats = Stats()

    def loadTimeService(self):
        try:
            with open(self.saveFileManager.get_save_path("timeService.json"), "r") as timeServiceSaveFile:
                self.timeService = self.timeServiceJsonReaderWriter.readTimeServiceFromFile(
                    timeServiceSaveFile, self.player, self.stats
                )
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"\n Warning: Failed to load time service data: {e}")
            print(" Creating new time service...")
            self.timeService = TimeService(self.player, self.stats)


if __name__ == "__main__":
    game = FishE()
    game.play()
