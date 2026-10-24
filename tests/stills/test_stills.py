"""The location stills (RFC 0025): one picture per place, shipped in game.zip,
shown above that place's menu wherever a front-end can draw one."""

import importlib.util
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fishE import FishE  # noqa: E402
from housing import housing  # noqa: E402
from location.enum.locationType import LocationType  # noqa: E402
from player.player import Player  # noqa: E402
from prompt.prompt import Prompt  # noqa: E402
from stats.stats import Stats  # noqa: E402
from stills import stills  # noqa: E402
from ui.consoleUserInterface import ConsoleUserInterface  # noqa: E402
from world.timeService import TimeService  # noqa: E402

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST = os.path.join(REPOSITORY_ROOT, "art", "stills.json")
PLACES = [
    LocationType.BANK,
    LocationType.DOCKS,
    LocationType.HOME,
    LocationType.SHOP,
    LocationType.TAVERN,
]


def manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def pngSize(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


def renderScript():
    spec = importlib.util.spec_from_file_location(
        "render", os.path.join(REPOSITORY_ROOT, "art", "render.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def homelessPlayer():
    player = Player()
    player.homeTier = 0
    return player


def rentingPlayer():
    player = Player()
    player.homeTier = 1
    return player


def test_every_place_has_one_still_with_alt_text_a_scene_and_a_picture():
    data = manifest()
    assert sorted(data["stills"]) == sorted(PLACES)
    width, height = data["size"]
    for place, entry in data["stills"].items():
        assert entry["alt"].strip(), place
        assert os.path.exists(os.path.join(REPOSITORY_ROOT, entry["scene"])), place
        png = os.path.join(REPOSITORY_ROOT, "pictures", place + ".png")
        assert pngSize(png) == (width, height), place


def test_the_setting_is_marked_provisional_and_every_sun_is_placed():
    data = manifest()
    assert data["provisional"] is True
    for place, entry in data["stills"].items():
        for field in ("date", "time", "utcOffset", "latitude", "longitude"):
            assert entry["sun"][field] not in (None, ""), (place, field)


def test_the_pictures_fit_the_budget():
    budget = manifest()["budgetBytes"]
    pictures = os.path.join(REPOSITORY_ROOT, "pictures")
    used = sum(os.path.getsize(os.path.join(pictures, n)) for n in os.listdir(pictures))
    assert used <= budget, used


def test_the_render_script_refuses_a_still_whose_sun_is_not_filled_in():
    render = renderScript()
    still = {
        "sun": {
            "date": "2023-09-21",
            "time": "08:00",
            "utcOffset": 1,
            "latitude": None,
            "longitude": "",
        }
    }
    assert render.sunProblems("docks", still) == [
        "docks: sun.latitude is not filled in",
        "docks: sun.longitude is not filled in",
    ]
    assert render.sunProblems("docks", {}) == ['docks: no "sun" entry']


def test_the_render_script_appends_the_sun_as_one_scene_line():
    sun = manifest()["stills"]["docks"]["sun"]
    assert renderScript().sunLine(sun) == "sun date 2023-09-21 08:00 1 54.5 -0.6"


def test_the_render_script_passes_its_own_check():
    assert renderScript().main(["--check"]) == 0


def test_load_reads_the_alt_text_and_tolerates_a_missing_manifest(tmp_path):
    assert sorted(stills.load(MANIFEST)) == sorted(PLACES)
    assert stills.load(str(tmp_path / "nowhere.json")) == {}
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    assert stills.load(str(broken)) == {}


def test_show_sets_a_places_picture_and_clears_it_for_a_place_without_one():
    ui = ConsoleUserInterface(Prompt(""), TimeService(Player(), Stats()), Player())
    alts = {LocationType.DOCKS: "The docks."}
    stills.show(ui, LocationType.DOCKS, alts, Player())
    assert ui.picture() == {"key": "docks", "alt": "The docks."}
    stills.show(ui, LocationType.SHOP, alts, Player())
    assert ui.picture() is None


def test_home_shows_no_room_to_a_player_with_nowhere_to_stay():
    assert housing.tierInfo(0)["status"] == "homeless"
    assert stills.placeShown(LocationType.HOME, homelessPlayer()) is None
    assert stills.placeShown(LocationType.HOME, rentingPlayer()) == LocationType.HOME
    assert stills.placeShown(LocationType.DOCKS, homelessPlayer()) == "docks"


class RecordingLocation:
    """Stands in for a place: records the picture its menu would be drawn
    under, then moves on to the next place in the script."""

    def __init__(self, ui, seen, nextLocation):
        self.ui = ui
        self.seen = seen
        self.nextLocation = nextLocation

    def run(self):
        self.seen.append((self.ui.picture() or {}).get("key"))
        return self.nextLocation


def test_each_place_is_drawn_under_its_own_still(monkeypatch):
    # The game loop sets the place's picture before running it - the same
    # loop every front-end plays through.
    monkeypatch.chdir(REPOSITORY_ROOT)
    game = FishE.__new__(FishE)
    game.running = True
    game.player = rentingPlayer()
    game.stats = Stats()
    game.timeService = TimeService(game.player, game.stats)
    game.prompt = Prompt("What would you like to do?")
    game.userInterface = ConsoleUserInterface(
        game.prompt, game.timeService, game.player
    )
    game.stillAlts = stills.load()
    game.save = lambda: None
    seen = []
    route = [
        LocationType.DOCKS,
        LocationType.SHOP,
        LocationType.BANK,
        LocationType.TAVERN,
        LocationType.HOME,
        LocationType.NONE,
    ]
    game.locations = {
        place: RecordingLocation(game.userInterface, seen, route[i + 1])
        for i, place in enumerate(route[:-1])
    }
    game.currentLocation = LocationType.DOCKS

    game._runGameLoop()

    assert seen == ["docks", "shop", "bank", "tavern", "home"]


def test_the_console_prints_nothing_for_a_picture(capsys):
    ui = ConsoleUserInterface(Prompt(""), TimeService(Player(), Stats()), Player())
    ui.setPicture("docks", "The docks.")
    assert capsys.readouterr().out == ""
