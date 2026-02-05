import os
import json
import shutil
from datetime import datetime


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
        # Look for save slots (slot_1, slot_2, etc.)
        for i in range(1, 100):  # Support up to 99 save slots
            slot_name = f"slot_{i}"
            slot_path = os.path.join(self.data_directory, slot_name)
            if os.path.exists(slot_path):
                metadata = self._read_save_metadata(slot_path)
                if metadata:
                    save_files.append(
                        {
                            "slot": i,
                            "slot_name": slot_name,
                            "path": slot_path,
                            "metadata": metadata,
                        }
                    )
        return save_files

    def _read_save_metadata(self, slot_path):
        """Read metadata from a save slot"""
        try:
            player_file = os.path.join(slot_path, "player.json")
            time_file = os.path.join(slot_path, "timeService.json")

            if not os.path.exists(player_file):
                return None

            metadata = {}

            # Read player data
            if os.path.exists(player_file) and os.path.getsize(player_file) > 0:
                with open(player_file, "r") as f:
                    player_data = json.load(f)
                    metadata["money"] = player_data.get("money", 0)
                    metadata["fishCount"] = player_data.get("fishCount", 0)
                    metadata["energy"] = player_data.get("energy", 100)

            # Read time data
            if os.path.exists(time_file) and os.path.getsize(time_file) > 0:
                with open(time_file, "r") as f:
                    time_data = json.load(f)
                    metadata["day"] = time_data.get("day", 1)
                    metadata["time"] = time_data.get("time", 0)

            # Get last modified time
            metadata["last_modified"] = datetime.fromtimestamp(
                os.path.getmtime(player_file)
            ).strftime("%Y-%m-%d %H:%M:%S")

            return metadata
        except Exception:
            return None

    def get_next_available_slot(self):
        """Returns the next available save slot number"""
        save_files = self.list_save_files()
        if not save_files:
            return 1
        
        # Find gaps in slot numbers
        existing_slots = sorted([save["slot"] for save in save_files])
        for i in range(1, 100):
            if i not in existing_slots:
                return i
        return len(existing_slots) + 1

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
            os.makedirs(slot_path)
        
        return os.path.join(slot_path, filename)

    def delete_save_slot(self, slot_number):
        """Delete a save slot"""
        slot_name = f"slot_{slot_number}"
        slot_path = os.path.join(self.data_directory, slot_name)
        
        if os.path.exists(slot_path):
            shutil.rmtree(slot_path)
            return True
        return False
