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
        """Move a pre-slot save (data/*.json) into a slot, if there is one.

        The save goes into slot_1 when slot_1 is free, otherwise into the next
        free slot: an existing slot is never written over. (Before cloud saves
        that could only happen with a hand-copied file; now a save set brought
        in from another device can hold both layouts, and the one already in
        a slot must survive.) With every slot taken, nothing is moved and the
        old files stay where they are."""
        old_player = os.path.join(self.data_directory, "player.json")
        old_files = ["player.json", "stats.json", "timeService.json"]

        # Check if old save files exist
        if not os.path.exists(old_player):
            return False

        # The kit's rule: the lowest slot whose directory holds no file.
        slot_number = self.get_next_available_slot()
        if slot_number is None:
            return False
        slot_path = os.path.join(self.data_directory, "slot_%d" % slot_number)
        os.makedirs(slot_path, exist_ok=True)

        # Move files into the slot. The slot held no file, so nothing in it is
        # replaced; a name that is somehow there already is left alone.
        try:
            for name in old_files:
                source = os.path.join(self.data_directory, name)
                target = os.path.join(slot_path, name)
                if os.path.exists(source) and not os.path.exists(target):
                    shutil.move(source, target)
            # The migration rewrote the save directory's layout; flush it so a
            # browser-storage player doesn't re-migrate on every page load.
            syncBrowserSaves()
            return True
        except (IOError, OSError):
            return False
