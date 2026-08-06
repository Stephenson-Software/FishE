import os
import json
import shutil
from datetime import datetime

from browserSaveSync import syncBrowserSaves


# @author Daniel McCoy Stephenson
class SaveFileManager:
    """Manages multiple save files for the game"""

    def __init__(self, data_directory="data"):
        self.data_directory = data_directory
        self.selected_save_slot = None

    def list_save_files(self):
        """Returns a list of available save file slots with their metadata"""
        if not os.path.exists(self.data_directory):
            return []

        save_files = []
        # Look for save slots (slot_1, slot_2, etc.) by inspecting existing directories
        try:
            for entry in os.listdir(self.data_directory):
                if not entry.startswith("slot_"):
                    continue

                # Extract the numeric slot index from the directory name
                _, _, suffix = entry.partition("_")
                if not suffix.isdigit():
                    continue

                slot_index = int(suffix)
                if slot_index < 1 or slot_index >= 100:
                    # Preserve the upper bound of 99 save slots
                    continue

                slot_name = entry
                slot_path = os.path.join(self.data_directory, slot_name)
                if not os.path.isdir(slot_path):
                    continue

                metadata = self._read_save_metadata(slot_path)
                if metadata:
                    save_files.append(
                        {
                            "slot": slot_index,
                            "slot_name": slot_name,
                            "path": slot_path,
                            "metadata": metadata,
                        }
                    )
        except OSError:
            # If we can't read the directory, return empty list
            return []

        return save_files

    def _read_save_metadata(self, slot_path):
        """Read metadata from a save slot.

        Returns None only when the slot holds no run at all (no player.json).
        A player.json that will not parse comes back as the marker described in
        _unreadable_save_metadata rather than as None, so a damaged slot stays
        listed and stays claimed instead of disappearing."""
        player_file = os.path.join(slot_path, "player.json")
        time_file = os.path.join(slot_path, "timeService.json")

        if not os.path.exists(player_file):
            return None

        metadata = {}

        # player.json is the file that holds the run, so it is read strictly.
        # Deliberately no "size > 0" guard: an empty file is a damaged file
        # rather than an absent one, and skipping the read for it is what let a
        # zero-byte save be offered in the menu as a real one.
        try:
            with open(player_file, "r") as f:
                player_data = json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as error:
            return self._unreadable_save_metadata(player_file, error)

        if not isinstance(player_data, dict):
            # Valid JSON that is not an object - a bare number, or some other
            # file copied over the save - has no fields to read, and .get()
            # would raise AttributeError here, taking the whole menu down with
            # it rather than reporting one bad slot.
            return self._unreadable_save_metadata(
                player_file, ValueError("not a JSON object")
            )

        metadata["money"] = player_data.get("money", 0)
        metadata["fishCount"] = player_data.get("fishCount", 0)
        metadata["energy"] = player_data.get("energy", 100)

        # The calendar is not the run: a slot whose timeService.json is missing
        # or damaged still holds a loadable player, and FishE reports and
        # preserves that damage on load. So this read is tolerant - leaving the
        # fields out just falls the menu label back to its "Day 1" default.
        try:
            with open(time_file, "r") as f:
                time_data = json.load(f)
            if isinstance(time_data, dict):
                metadata["day"] = time_data.get("day", 1)
                metadata["time"] = time_data.get("time", 0)
        except (json.JSONDecodeError, IOError, OSError):
            pass

        metadata["last_modified"] = self._last_modified(player_file)

        return metadata

    def _last_modified(self, path):
        """A file's modification time as a display string, or None if unknown."""
        try:
            return datetime.fromtimestamp(os.path.getmtime(path)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except OSError:
            return None

    def _unreadable_save_metadata(self, player_file, error):
        """Metadata standing in for a slot whose player.json will not parse.

        Returned instead of None because list_save_files() drops a slot with no
        metadata, and get_next_available_slot() derives the taken slot numbers
        from that same filtered list - so a damaged slot used to vanish from the
        menu *and* be handed straight back as "Create New Save", pointing the
        next save at the occupied directory and overwriting the intact
        stats.json and timeService.json sitting beside the damaged file.

        Callers key off "unreadable" to show the slot as present but unpickable
        (see FishE._selectSaveFile)."""
        return {
            "unreadable": True,
            "reason": str(error),
            "last_modified": self._last_modified(player_file),
        }

    def get_next_available_slot(self):
        """Returns the next available save slot number, or None if all slots are full"""
        save_files = self.list_save_files()
        if not save_files:
            return 1

        # Find gaps in slot numbers
        existing_slots = sorted([save["slot"] for save in save_files])
        for i in range(1, 100):
            if i not in existing_slots:
                return i
        # All 99 slots are full
        return None

    def select_save_slot(self, slot_number):
        """Select a save slot to use"""
        self.selected_save_slot = slot_number

    def get_save_path(self, filename):
        """Get the full path for a save file in the selected slot"""
        if self.selected_save_slot is None:
            raise ValueError("No save slot selected")

        slot_name = f"slot_{self.selected_save_slot}"
        slot_path = os.path.join(self.data_directory, slot_name)

        # Create slot directory if it doesn't exist
        if not os.path.exists(slot_path):
            os.makedirs(slot_path, exist_ok=True)

        return os.path.join(slot_path, filename)

    def delete_save_slot(self, slot_number):
        """Delete a save slot"""
        slot_name = f"slot_{slot_number}"
        slot_path = os.path.join(self.data_directory, slot_name)

        if os.path.exists(slot_path):
            shutil.rmtree(slot_path)
            # Browser storage mirrors the save directory wholesale, so a
            # deletion has to be flushed too — otherwise the slot comes back
            # on the next page load. A no-op outside the Pyodide front-end.
            syncBrowserSaves()
            return True
        return False

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
