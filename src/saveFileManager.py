import os
import json
import shutil

from tak.saves import SaveFileManager as KitSaveFileManager
from tak.saves import syncBrowserSaves


def readSlotMetadata(slot_path, player_data):
    """FishE's summary of a slot, for the save menu.

    player.json has already been read strictly by the kit (a damaged one never
    reaches here). The calendar is not the run: a slot whose timeService.json
    is missing or damaged still holds a loadable player, and FishE reports
    and preserves that damage on load - so this read is tolerant, leaving the
    fields out just falls the menu label back to its "Day 1" default."""
    metadata = {
        "money": player_data.get("money", 0),
        "fishCount": player_data.get("fishCount", 0),
        "energy": player_data.get("energy", 100),
    }
    time_file = os.path.join(slot_path, "timeService.json")
    try:
        with open(time_file, "r") as f:
            time_data = json.load(f)
        if isinstance(time_data, dict):
            metadata["day"] = time_data.get("day", 1)
            metadata["time"] = time_data.get("time", 0)
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return metadata


# @author Daniel McCoy Stephenson
class SaveFileManager(KitSaveFileManager):
    """FishE's save slots: the kit's numbered-slot manager with player.json as
    the file that means "there is a save here", FishE's menu summary, and the
    one-time migration of the pre-slot layout."""

    def __init__(self, data_directory="data"):
        super().__init__(
            data_directory, primaryFile="player.json", readMetadata=readSlotMetadata
        )

    def migrate_old_save_files(self):
        """Migrate old save files (data/*.json) to slot_1 if they exist"""
        old_player = os.path.join(self.data_directory, "player.json")
        old_stats = os.path.join(self.data_directory, "stats.json")
        old_time = os.path.join(self.data_directory, "timeService.json")

        # Check if old save files exist
        if not os.path.exists(old_player):
            return False

        # Create slot_1 directory
        slot_1_path = os.path.join(self.data_directory, "slot_1")
        if not os.path.exists(slot_1_path):
            os.makedirs(slot_1_path, exist_ok=True)

        # Move files to slot_1
        try:
            if os.path.exists(old_player):
                shutil.move(old_player, os.path.join(slot_1_path, "player.json"))
            if os.path.exists(old_stats):
                shutil.move(old_stats, os.path.join(slot_1_path, "stats.json"))
            if os.path.exists(old_time):
                shutil.move(old_time, os.path.join(slot_1_path, "timeService.json"))
            # The migration rewrote the save directory's layout; flush it so a
            # browser-storage player doesn't re-migrate on every page load.
            syncBrowserSaves()
            return True
        except (IOError, OSError):
            return False
