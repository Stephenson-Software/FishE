import os
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


# @author Daniel McCoy Stephenson
class FishE:
    def __init__(self):
        self.running = True

        self.playerJsonReaderWriter = PlayerJsonReaderWriter()
        self.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
        self.statsJsonReaderWriter = StatsJsonReaderWriter()
        self.saveFileManager = SaveFileManager()

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
        print(f" [N] Create New Save (Slot {next_slot})")
        if save_files:
            print(" [D] Delete a Save File")
        print(" [Q] Quit")
        print("-" * 75)

        while True:
            choice = input("\n Select an option: ").strip().upper()

            if choice == "Q":
                print("\n Goodbye!")
                exit(0)
            elif choice == "N":
                self.saveFileManager.select_save_slot(next_slot)
                print(f"\n Creating new save in Slot {next_slot}...")
                break
            elif choice == "D" and save_files:
                self._deleteSaveFile(save_files)
                # Recursively call to show updated menu
                self._selectSaveFile()
                return
            elif choice.isdigit():
                slot_num = int(choice)
                if any(save["slot"] == slot_num for save in save_files):
                    self.saveFileManager.select_save_slot(slot_num)
                    print(f"\n Loading Save Slot {slot_num}...")
                    break
                else:
                    print(" Invalid slot number. Try again.")
            else:
                print(" Invalid choice. Try again.")

    def _deleteSaveFile(self, save_files):
        """Delete a save file"""
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
                return
            elif choice.isdigit():
                slot_num = int(choice)
                if any(save["slot"] == slot_num for save in save_files):
                    confirm = input(f"\n Are you sure you want to delete Slot {slot_num}? (Y/N): ").strip().upper()
                    if confirm == "Y":
                        if self.saveFileManager.delete_save_slot(slot_num):
                            print(f"\n Slot {slot_num} deleted successfully.")
                            input("\n [ CONTINUE ]")
                            return
                        else:
                            print(f"\n Failed to delete Slot {slot_num}.")
                    else:
                        return
                else:
                    print(" Invalid slot number. Try again.")
            else:
                print(" Invalid choice. Try again.")

    def play(self):
        while self.running:
            # change location
            nextLocation = self.locations[self.currentLocation].run()

            if nextLocation == LocationType.NONE:
                self.running = False

            self.currentLocation = nextLocation

            # increase time & save
            self.timeService.increaseTime()
            self.save()

    def save(self):
        # create data directory
        if not os.path.exists("data"):
            os.makedirs("data")

        playerSaveFile = open(self.saveFileManager.get_save_path("player.json"), "w")
        self.playerJsonReaderWriter.writePlayerToFile(self.player, playerSaveFile)
        playerSaveFile.close()

        timeServiceSaveFile = open(
            self.saveFileManager.get_save_path("timeService.json"), "w"
        )
        self.timeServiceJsonReaderWriter.writeTimeServiceToFile(
            self.timeService, timeServiceSaveFile
        )
        timeServiceSaveFile.close()

        statsSaveFile = open(self.saveFileManager.get_save_path("stats.json"), "w")
        self.statsJsonReaderWriter.writeStatsToFile(self.stats, statsSaveFile)
        statsSaveFile.close()

    def loadPlayer(self):
        playerSaveFile = open(self.saveFileManager.get_save_path("player.json"), "r")
        self.player = self.playerJsonReaderWriter.readPlayerFromFile(playerSaveFile)
        playerSaveFile.close()

    def loadStats(self):
        statsSaveFile = open(self.saveFileManager.get_save_path("stats.json"), "r")
        self.stats = self.statsJsonReaderWriter.readStatsFromFile(statsSaveFile)
        statsSaveFile.close()

    def loadTimeService(self):
        timeServiceSaveFile = open(
            self.saveFileManager.get_save_path("timeService.json"), "r"
        )
        self.timeService = self.timeServiceJsonReaderWriter.readTimeServiceFromFile(
            timeServiceSaveFile, self.player, self.stats
        )
        timeServiceSaveFile.close()


if __name__ == "__main__":
    FishE = FishE()
    FishE.play()
