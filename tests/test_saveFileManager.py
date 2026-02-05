import os
import json
import tempfile
import shutil
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


def test_select_save_slot():
    manager = SaveFileManager()
    manager.select_save_slot(5)
    assert manager.selected_save_slot == 5


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


def test_get_save_path_no_slot_selected():
    manager = SaveFileManager()
    try:
        manager.get_save_path("player.json")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No save slot selected" in str(e)


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
