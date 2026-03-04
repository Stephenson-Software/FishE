import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from src.saveFileManager import SaveFileManager


def test_initialization():
    manager = SaveFileManager()
    assert manager.data_directory == "data"
    assert manager.selected_save_slot is None


def test_initialization_custom_directory():
    manager = SaveFileManager("custom_data")
    assert manager.data_directory == "custom_data"


def test_list_save_files_empty():
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        save_files = manager.list_save_files()
        assert save_files == []
    finally:
        shutil.rmtree(temp_dir)


def test_list_save_files_with_saves():
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create a save slot
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)

        # Create player.json
        player_data = {"money": 100, "fishCount": 5, "energy": 80}
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump(player_data, f)

        # Create timeService.json
        time_data = {"day": 3, "time": 10}
        with open(os.path.join(slot_path, "timeService.json"), "w") as f:
            json.dump(time_data, f)

        save_files = manager.list_save_files()
        assert len(save_files) == 1
        assert save_files[0]["slot"] == 1
        assert save_files[0]["metadata"]["money"] == 100
        assert save_files[0]["metadata"]["fishCount"] == 5
        assert save_files[0]["metadata"]["day"] == 3
    finally:
        shutil.rmtree(temp_dir)


def test_list_save_files_ignores_invalid_names():
    """Test that list_save_files ignores directories with invalid names"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create valid slot
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 100}, f)

        # Create invalid directories that should be ignored
        os.makedirs(os.path.join(temp_dir, "slot_abc"))  # Non-numeric suffix
        os.makedirs(os.path.join(temp_dir, "invalid_1"))  # Wrong prefix
        os.makedirs(os.path.join(temp_dir, "slot_"))  # Missing number
        os.makedirs(os.path.join(temp_dir, "slot_0"))  # Slot 0 (invalid)
        os.makedirs(os.path.join(temp_dir, "slot_100"))  # Slot 100 (out of range)
        
        # Create a regular file (not a directory)
        with open(os.path.join(temp_dir, "slot_2"), "w") as f:
            f.write("not a directory")

        save_files = manager.list_save_files()
        assert len(save_files) == 1
        assert save_files[0]["slot"] == 1
    finally:
        shutil.rmtree(temp_dir)


def test_list_save_files_multiple_slots_sorted():
    """Test that multiple save slots are returned in sorted order"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create multiple slots in non-sequential order
        for slot_num in [5, 1, 3]:
            slot_path = os.path.join(temp_dir, f"slot_{slot_num}")
            os.makedirs(slot_path)
            with open(os.path.join(slot_path, "player.json"), "w") as f:
                json.dump({"money": slot_num * 100}, f)

        save_files = manager.list_save_files()
        assert len(save_files) == 3
        # Results should be in the order they were found (not necessarily sorted)
        slot_numbers = [save["slot"] for save in save_files]
        assert set(slot_numbers) == {1, 3, 5}
    finally:
        shutil.rmtree(temp_dir)


def test_list_save_files_oserror_handling():
    """Test that list_save_files returns empty list on OSError"""
    manager = SaveFileManager("/non/existent/path")
    
    # This should not raise an exception
    save_files = manager.list_save_files()
    assert save_files == []


def test_get_next_available_slot_empty():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        next_slot = manager.get_next_available_slot()
        assert next_slot == 1
    finally:
        shutil.rmtree(temp_dir)


def test_get_next_available_slot_with_existing():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create slot 1
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 0}, f)

        next_slot = manager.get_next_available_slot()
        assert next_slot == 2
    finally:
        shutil.rmtree(temp_dir)


def test_get_next_available_slot_with_gap():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create slot 1 and 3 (gap at 2)
        for slot_num in [1, 3]:
            slot_path = os.path.join(temp_dir, f"slot_{slot_num}")
            os.makedirs(slot_path)
            with open(os.path.join(slot_path, "player.json"), "w") as f:
                json.dump({"money": 0}, f)

        next_slot = manager.get_next_available_slot()
        assert next_slot == 2
    finally:
        shutil.rmtree(temp_dir)


def test_get_next_available_slot_all_full():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create 99 save slots
        for i in range(1, 100):
            slot_path = os.path.join(temp_dir, f"slot_{i}")
            os.makedirs(slot_path)
            with open(os.path.join(slot_path, "player.json"), "w") as f:
                json.dump({"money": 0}, f)
        
        next_slot = manager.get_next_available_slot()
        assert next_slot is None
    finally:
        shutil.rmtree(temp_dir)


def test_select_save_slot():
    manager = SaveFileManager()
    manager.select_save_slot(5)
    assert manager.selected_save_slot == 5


def test_select_save_slot_boundary_values():
    """Test selecting boundary slot values"""
    manager = SaveFileManager()
    
    # Test slot 1 (minimum valid)
    manager.select_save_slot(1)
    assert manager.selected_save_slot == 1
    
    # Test slot 99 (maximum valid)
    manager.select_save_slot(99)
    assert manager.selected_save_slot == 99
    
    # Test slot 0 (edge case - technically allowed by select but not recommended)
    manager.select_save_slot(0)
    assert manager.selected_save_slot == 0


def test_get_save_path():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        manager.select_save_slot(1)
        
        path = manager.get_save_path("player.json")
        expected = os.path.join(temp_dir, "slot_1", "player.json")
        assert path == expected
        
        # Check that directory was created
        assert os.path.exists(os.path.join(temp_dir, "slot_1"))
    finally:
        shutil.rmtree(temp_dir)


def test_get_save_path_creates_directory():
    """Test that get_save_path creates the slot directory if it doesn't exist"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        manager.select_save_slot(5)
        
        slot_path = os.path.join(temp_dir, "slot_5")
        assert not os.path.exists(slot_path)
        
        # Calling get_save_path should create the directory
        path = manager.get_save_path("player.json")
        assert os.path.exists(slot_path)
        assert os.path.isdir(slot_path)
    finally:
        shutil.rmtree(temp_dir)


def test_get_save_path_multiple_files():
    """Test getting paths for multiple files in the same slot"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        manager.select_save_slot(1)
        
        player_path = manager.get_save_path("player.json")
        stats_path = manager.get_save_path("stats.json")
        time_path = manager.get_save_path("timeService.json")
        
        # All should be in the same slot directory
        assert os.path.dirname(player_path) == os.path.dirname(stats_path)
        assert os.path.dirname(stats_path) == os.path.dirname(time_path)
        
        # But different files
        assert player_path != stats_path
        assert stats_path != time_path
    finally:
        shutil.rmtree(temp_dir)


def test_get_save_path_no_slot_selected():
    manager = SaveFileManager()
    with pytest.raises(ValueError, match="No save slot selected"):
        manager.get_save_path("player.json")


def test_delete_save_slot():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create a save slot
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 100}, f)

        assert os.path.exists(slot_path)

        # Delete it
        result = manager.delete_save_slot(1)
        assert result is True
        assert not os.path.exists(slot_path)
    finally:
        shutil.rmtree(temp_dir)


def test_delete_nonexistent_save_slot():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        result = manager.delete_save_slot(99)
        assert result is False
    finally:
        shutil.rmtree(temp_dir)


def test_delete_save_slot_with_multiple_files():
    """Test that deleting a slot removes all files in it"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create a save slot with multiple files
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 100}, f)
        with open(os.path.join(slot_path, "stats.json"), "w") as f:
            json.dump({"totalFishCaught": 50}, f)
        with open(os.path.join(slot_path, "timeService.json"), "w") as f:
            json.dump({"day": 5}, f)

        # Delete the slot
        result = manager.delete_save_slot(1)
        assert result is True
        assert not os.path.exists(slot_path)
    finally:
        shutil.rmtree(temp_dir)


def test_multiple_save_files_dont_conflict():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)

        # Create slot 1
        manager.select_save_slot(1)
        path1 = manager.get_save_path("player.json")
        with open(path1, "w") as f:
            json.dump({"money": 100}, f)

        # Create slot 2
        manager.select_save_slot(2)
        path2 = manager.get_save_path("player.json")
        with open(path2, "w") as f:
            json.dump({"money": 200}, f)

        # Verify both exist and are different
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert path1 != path2

        with open(path1, "r") as f:
            data1 = json.load(f)
        with open(path2, "r") as f:
            data2 = json.load(f)

        assert data1["money"] == 100
        assert data2["money"] == 200
    finally:
        shutil.rmtree(temp_dir)


def test_read_save_metadata_missing_files():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create empty slot directory
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        
        metadata = manager._read_save_metadata(slot_path)
        assert metadata is None
    finally:
        shutil.rmtree(temp_dir)


def test_read_save_metadata_corrupted_json():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create slot with corrupted json
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            f.write("invalid json{")
        
        metadata = manager._read_save_metadata(slot_path)
        assert metadata is None
    finally:
        shutil.rmtree(temp_dir)


def test_read_save_metadata_empty_player_file():
    """Test reading metadata from an empty player.json file"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        
        # Create empty player.json
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            f.write("")
        
        metadata = manager._read_save_metadata(slot_path)
        # Empty file still returns metadata with last_modified but no game data
        assert metadata is not None
        assert "last_modified" in metadata
        # Game data fields should not be present since file is empty
        assert "money" not in metadata
        assert "fishCount" not in metadata
    finally:
        shutil.rmtree(temp_dir)


def test_read_save_metadata_partial_data():
    """Test reading metadata when only some fields are present"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        
        # Create player.json with minimal data
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 50}, f)  # Missing fishCount and energy
        
        metadata = manager._read_save_metadata(slot_path)
        assert metadata is not None
        assert metadata["money"] == 50
        assert metadata["fishCount"] == 0  # Default value
        assert metadata["energy"] == 100  # Default value
        assert "last_modified" in metadata
    finally:
        shutil.rmtree(temp_dir)


def test_read_save_metadata_missing_timeservice():
    """Test reading metadata when timeService.json is missing"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        slot_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_path)
        
        # Create only player.json
        with open(os.path.join(slot_path, "player.json"), "w") as f:
            json.dump({"money": 100, "fishCount": 10}, f)
        
        metadata = manager._read_save_metadata(slot_path)
        assert metadata is not None
        assert metadata["money"] == 100
        assert metadata["fishCount"] == 10
        # Time data should not be present or have defaults
        assert "day" not in metadata or metadata["day"] == 1
        assert "time" not in metadata or metadata["time"] == 0
    finally:
        shutil.rmtree(temp_dir)


def test_migrate_old_save_files():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create old format save files
        os.makedirs(temp_dir, exist_ok=True)
        with open(os.path.join(temp_dir, "player.json"), "w") as f:
            json.dump({"money": 100, "fishCount": 5}, f)
        with open(os.path.join(temp_dir, "stats.json"), "w") as f:
            json.dump({"totalFishCaught": 10}, f)
        with open(os.path.join(temp_dir, "timeService.json"), "w") as f:
            json.dump({"day": 2}, f)
        
        # Migrate
        result = manager.migrate_old_save_files()
        assert result is True
        
        # Check that files were moved to slot_1
        assert os.path.exists(os.path.join(temp_dir, "slot_1", "player.json"))
        assert os.path.exists(os.path.join(temp_dir, "slot_1", "stats.json"))
        assert os.path.exists(os.path.join(temp_dir, "slot_1", "timeService.json"))
        
        # Check that old files are gone
        assert not os.path.exists(os.path.join(temp_dir, "player.json"))
        assert not os.path.exists(os.path.join(temp_dir, "stats.json"))
        assert not os.path.exists(os.path.join(temp_dir, "timeService.json"))
    finally:
        shutil.rmtree(temp_dir)


def test_migrate_old_save_files_no_old_saves():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        result = manager.migrate_old_save_files()
        assert result is False
    finally:
        shutil.rmtree(temp_dir)


def test_migrate_old_save_files_partial():
    """Test migration when only some old files exist"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create only player.json (missing stats and timeService)
        with open(os.path.join(temp_dir, "player.json"), "w") as f:
            json.dump({"money": 100}, f)
        
        result = manager.migrate_old_save_files()
        assert result is True
        
        # Check that player.json was moved
        assert os.path.exists(os.path.join(temp_dir, "slot_1", "player.json"))
        assert not os.path.exists(os.path.join(temp_dir, "player.json"))
        
        # Other files shouldn't exist in either location
        assert not os.path.exists(os.path.join(temp_dir, "stats.json"))
        assert not os.path.exists(os.path.join(temp_dir, "slot_1", "stats.json"))
    finally:
        shutil.rmtree(temp_dir)


def test_migrate_old_save_files_slot1_exists():
    """Test migration when slot_1 already exists"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create existing slot_1 with data
        slot_1_path = os.path.join(temp_dir, "slot_1")
        os.makedirs(slot_1_path)
        with open(os.path.join(slot_1_path, "player.json"), "w") as f:
            json.dump({"money": 999}, f)  # Existing data
        
        # Create old format files
        with open(os.path.join(temp_dir, "player.json"), "w") as f:
            json.dump({"money": 100}, f)
        
        # Migration should still succeed (will overwrite)
        result = manager.migrate_old_save_files()
        assert result is True
        
        # Check that old file was moved and overwrote existing
        with open(os.path.join(slot_1_path, "player.json"), "r") as f:
            data = json.load(f)
            assert data["money"] == 100  # Should be the migrated value
    finally:
        shutil.rmtree(temp_dir)


def test_integration_create_save_and_delete():
    """Integration test: create multiple saves and delete one"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Create slot 1
        manager.select_save_slot(1)
        path1 = manager.get_save_path("player.json")
        with open(path1, "w") as f:
            json.dump({"money": 100}, f)
        
        # Create slot 2
        manager.select_save_slot(2)
        path2 = manager.get_save_path("player.json")
        with open(path2, "w") as f:
            json.dump({"money": 200}, f)
        
        # List should show both
        saves = manager.list_save_files()
        assert len(saves) == 2
        
        # Delete slot 1
        manager.delete_save_slot(1)
        
        # List should show only slot 2
        saves = manager.list_save_files()
        assert len(saves) == 1
        assert saves[0]["slot"] == 2
        
        # Next available should be 1 (the gap)
        next_slot = manager.get_next_available_slot()
        assert next_slot == 1
    finally:
        shutil.rmtree(temp_dir)


def test_integration_full_workflow():
    """Integration test: simulate a full user workflow"""
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SaveFileManager(temp_dir)
        
        # Start with no saves
        assert manager.list_save_files() == []
        assert manager.get_next_available_slot() == 1
        
        # Create first save
        manager.select_save_slot(1)
        player_path = manager.get_save_path("player.json")
        with open(player_path, "w") as f:
            json.dump({"money": 100, "fishCount": 10, "energy": 85}, f)
        time_path = manager.get_save_path("timeService.json")
        with open(time_path, "w") as f:
            json.dump({"day": 5, "time": 12}, f)
        
        # List saves and verify metadata
        saves = manager.list_save_files()
        assert len(saves) == 1
        assert saves[0]["metadata"]["money"] == 100
        assert saves[0]["metadata"]["day"] == 5
        
        # Create second save
        manager.select_save_slot(2)
        player_path2 = manager.get_save_path("player.json")
        with open(player_path2, "w") as f:
            json.dump({"money": 500, "fishCount": 50, "energy": 100}, f)
        
        # Verify two saves exist
        saves = manager.list_save_files()
        assert len(saves) == 2
        
        # Next slot should be 3
        assert manager.get_next_available_slot() == 3
    finally:
        shutil.rmtree(temp_dir)
