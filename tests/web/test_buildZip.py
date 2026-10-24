"""web/build_zip.py is a thin call into tak.web.bundle; these tests pin what
FishE puts in the bundle."""

import os
import zipfile

from tak.web.bundle import build

from web.build_zip import EXTRA_FILES, REPOSITORY_ROOT, SOURCE_DIRECTORIES


def buildBundle(tmp_path):
    outputPath = tmp_path / "game.zip"
    build(
        REPOSITORY_ROOT,
        outputPath=str(outputPath),
        sourceDirectories=SOURCE_DIRECTORIES,
        extraFiles=EXTRA_FILES,
    )
    with zipfile.ZipFile(outputPath) as bundle:
        return set(bundle.namelist())


def test_bundle_carries_the_location_stills_but_not_their_scenes(tmp_path):
    # RFC 0025: the pictures and the manifest naming them ride in the bundle
    # (the Worker reads /game/pictures/<key>.png); the scene files do not.
    names = buildBundle(tmp_path)
    assert "art/stills.json" in names
    for place in ("bank", "docks", "home", "shop", "tavern"):
        assert "pictures/%s.png" % place in names, place
    assert not any(name.endswith(".scene") for name in names)


def test_bundle_carries_the_game(tmp_path):
    names = buildBundle(tmp_path)
    assert "src/fishE.py" in names
    assert "src/location/docks.py" in names


def test_bundle_carries_the_usage_reporting_modules(tmp_path):
    names = buildBundle(tmp_path)
    assert "src/usageReporting.py" in names
    assert "src/trace_client.py" in names


def test_bundle_carries_the_schemas_the_save_readers_validate_against(tmp_path):
    names = buildBundle(tmp_path)
    for schema in ("player.json", "stats.json", "timeService.json"):
        assert "schemas/" + schema in names, schema


def test_bundle_carries_the_worker_entry_point_and_version(tmp_path):
    names = buildBundle(tmp_path)
    assert "web/pyodide_main.py" in names
    assert "version.txt" in names


def test_bundle_carries_the_kit_under_src(tmp_path):
    # One sys.path entry (/game/src) covers the game and the kit it imports.
    names = buildBundle(tmp_path)
    for module in (
        "__init__.py",
        "ui/pyodide.py",
        "saves/manager.py",
        "progression.py",
    ):
        assert "src/tak/" + module in names, module


def test_bundle_excludes_build_artifacts(tmp_path):
    names = buildBundle(tmp_path)
    assert not any(name.endswith(".pyc") or "__pycache__" in name for name in names)
    assert "web/game.zip" not in names
