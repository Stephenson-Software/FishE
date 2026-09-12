"""Usage reporting: what is sent, the opt-out, and the first-run notice.

Every enabled client here points at a loopback stub server, never at the
production service; the autouse fixture in conftest.py keeps everything else
off. Imported bare (not "src."-prefixed) the way fishE.py imports it, so the
module patched here is the one the game uses.
"""

import io
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import pytest

import usageReporting
from config.config import Config
from src import fishE
from src.player.player import Player
from src.stats.stats import Stats


class StubTrace:
    """The smallest thing that accepts what the client posts and remembers it."""

    def __init__(self):
        self.requests = []
        self.arrived = threading.Event()
        capture = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                capture.requests.append(
                    {
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                        "body": json.loads(body.decode("utf-8")),
                    }
                )
                self.send_response(201)
                self.send_header("Content-Length", "0")
                self.end_headers()
                capture.arrived.set()

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]

    def waitFor(self, count, timeout=5):
        pause = threading.Event()
        for _ in range(int(timeout * 20)):
            if len(self.requests) >= count:
                return True
            pause.wait(0.05)
        return len(self.requests) >= count

    def close(self):
        self.server.shutdown()


@pytest.fixture
def stub():
    server = StubTrace()
    yield server
    server.close()


@pytest.fixture
def reportingOn(monkeypatch, stub, tmp_path):
    """Reporting on, aimed at the stub, with a fresh save directory."""
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", "true")
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENDPOINT", stub.url)
    monkeypatch.setenv("FISHE_USAGE_REPORTING_KEY", "test-key")
    monkeypatch.setenv("FISHE_SAVE_DIR", str(tmp_path / "saves"))
    return Config()


# -- the version tag ----------------------------------------------------------


def test_the_version_is_read_from_version_txt(tmp_path):
    versionFile = tmp_path / "version.txt"
    versionFile.write_text("9.9.9-TEST\n")

    assert usageReporting.readVersion(str(versionFile)) == "9.9.9-TEST"


def test_the_version_tag_is_what_version_txt_says(monkeypatch, tmp_path):
    versionFile = tmp_path / "version.txt"
    versionFile.write_text("9.9.9-TEST\n")
    monkeypatch.setattr(usageReporting, "VERSION_FILE", str(versionFile))

    assert usageReporting.versionTags() == {"version": "9.9.9-TEST"}


def test_the_repository_version_file_is_the_one_run_sh_prints():
    # The default path resolves to the checkout's version.txt, the same file
    # run.sh cats as "Current version".
    repositoryVersion = open(
        os.path.join(os.path.dirname(__file__), "..", "version.txt")
    ).read()

    assert usageReporting.readVersion() == repositoryVersion.strip()


def test_a_missing_or_empty_version_file_means_no_version_tag(monkeypatch, tmp_path):
    empty = tmp_path / "version.txt"
    empty.write_text("   \n")
    assert usageReporting.readVersion(str(tmp_path / "absent.txt")) is None
    assert usageReporting.readVersion(str(empty)) is None

    monkeypatch.setattr(usageReporting, "VERSION_FILE", str(tmp_path / "absent.txt"))

    assert usageReporting.versionTags() is None


# -- building the client ------------------------------------------------------


def test_reporting_is_on_by_default(reportingOn):
    client = usageReporting.createClient(reportingOn)

    assert client.enabled
    client.close()


def test_the_opt_out_yields_a_client_that_does_nothing(monkeypatch, reportingOn):
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", "false")

    client = usageReporting.createClient(Config())

    assert not client.enabled


def test_an_empty_key_yields_a_client_that_does_nothing(reportingOn):
    reportingOn.usageReportingKey = ""

    assert not usageReporting.createClient(reportingOn).enabled


def test_the_browser_build_never_reports(monkeypatch, reportingOn):
    # Pyodide has no OS threads or sockets: the client's sending thread could
    # not even be started there, so the browser build is refused outright.
    monkeypatch.setattr(sys, "platform", "emscripten")

    assert usageReporting.isBrowserBuild()
    assert not usageReporting.createClient(reportingOn).enabled


def test_the_application_is_the_name_the_key_was_issued_for():
    assert usageReporting.PROGRAM_NAME == "FishE"


# -- the first-run notice -----------------------------------------------------


def test_the_notice_is_printed_once_and_then_never_again(reportingOn):
    first, second, third = io.StringIO(), io.StringIO(), io.StringIO()

    assert usageReporting.showNoticeOnce(reportingOn, first) is True
    assert usageReporting.showNoticeOnce(reportingOn, second) is False
    assert usageReporting.showNoticeOnce(reportingOn, third) is False

    assert first.getvalue() == usageReporting.NOTICE + "\n"
    assert second.getvalue() == ""
    assert third.getvalue() == ""


def test_the_notice_names_the_program_what_is_sent_and_the_opt_out():
    assert usageReporting.NOTICE == (
        "Usage reporting is on: FishE sends a startup event and a save-loaded "
        "event (program name and version only) to trace.danielstephenson.dev. "
        "Turn it off with FISHE_USAGE_REPORTING_ENABLED=false in the environment."
    )
    assert "\n" not in usageReporting.NOTICE


def test_the_marker_lives_in_the_save_directory_and_says_what_it_is(reportingOn):
    usageReporting.showNoticeOnce(reportingOn, io.StringIO())

    markerPath = os.path.join(
        reportingOn.dataDirectory, usageReporting.NOTICE_MARKER_FILENAME
    )
    assert os.path.exists(markerPath)
    assert open(markerPath).read().strip() == usageReporting.NOTICE


def test_the_marker_does_not_read_as_a_save_slot(reportingOn):
    from src.saveFileManager import SaveFileManager

    usageReporting.showNoticeOnce(reportingOn, io.StringIO())

    assert SaveFileManager(reportingOn.dataDirectory).list_save_files() == []
    assert SaveFileManager(reportingOn.dataDirectory).get_next_available_slot() == 1


def test_an_unwritable_marker_still_prints_the_notice(reportingOn, tmp_path):
    # Being told twice is the lesser failure; the notice never blocks startup.
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the save directory would go")
    reportingOn.dataDirectory = str(blocker)
    output = io.StringIO()

    assert usageReporting.showNoticeOnce(reportingOn, output) is True
    assert output.getvalue() == usageReporting.NOTICE + "\n"


def test_start_prints_the_notice_and_reports_startup_with_the_version(
    reportingOn, stub
):
    output = io.StringIO()

    client = usageReporting.start(reportingOn, output)

    assert client.enabled
    assert output.getvalue() == usageReporting.NOTICE + "\n"
    assert stub.waitFor(1)
    request = stub.requests[0]
    assert request["path"] == "/api/metrics"
    assert request["authorization"] == "Bearer test-key"
    assert request["body"] == {
        "application": "FishE",
        "name": "startup",
        "tags": {"version": usageReporting.readVersion()},
    }
    client.close()


def test_start_says_nothing_and_sends_nothing_when_reporting_is_off(
    monkeypatch, reportingOn, stub
):
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", "0")
    output = io.StringIO()

    client = usageReporting.start(Config(), output)

    assert not client.enabled
    assert output.getvalue() == ""
    assert not os.path.exists(usageReporting.noticeMarkerPath(reportingOn))
    assert not stub.waitFor(1, timeout=0.5)


def test_the_second_start_reports_startup_again_but_stays_quiet(reportingOn, stub):
    first = usageReporting.start(reportingOn, io.StringIO())
    assert stub.waitFor(1)
    first.close()
    quiet = io.StringIO()

    second = usageReporting.start(reportingOn, quiet)
    assert stub.waitFor(2)
    second.close()

    assert [r["body"]["name"] for r in stub.requests] == ["startup", "startup"]
    assert quiet.getvalue() == ""


# -- wiring into the game -----------------------------------------------------


def createFishE(selectSaveFile):
    """A FishE with the collaborators the constructor needs mocked away, the
    save-file menu replaced by selectSaveFile, and reporting left real."""
    fishE.Player = MagicMock(return_value=Player())
    fishE.Stats = MagicMock(return_value=Stats())
    fishE.TimeService = MagicMock()
    fishE.Prompt = MagicMock()
    fishE.UserInterfaceFactory = MagicMock()
    fishE.bank.Bank = MagicMock()
    fishE.shop.Shop = MagicMock()
    fishE.home.Home = MagicMock()
    fishE.docks.Docks = MagicMock()
    fishE.tavern.Tavern = MagicMock()
    fishE.PlayerJsonReaderWriter = MagicMock()
    fishE.TimeServiceJsonReaderWriter = MagicMock()
    fishE.StatsJsonReaderWriter = MagicMock()
    fishE.SaveFileManager = MagicMock()
    saveFileManager = MagicMock()
    saveFileManager.get_save_path.return_value = "/nonexistent/player.json"
    saveFileManager.list_save_files.return_value = []
    fishE.SaveFileManager.return_value = saveFileManager
    with patch.object(fishE.FishE, "_selectSaveFile", selectSaveFile):
        return fishE.FishE()


def test_the_game_reports_startup_then_save_loaded(reportingOn, stub, capsys):
    game = createFishE(lambda self: None)
    assert stub.waitFor(2)
    # play() with the run already over does only what every ending does:
    # release the front-end and close the client.
    game.running = False
    game.userInterface = MagicMock()
    game.play()

    version = usageReporting.readVersion()
    assert [r["body"] for r in stub.requests] == [
        {"application": "FishE", "name": "startup", "tags": {"version": version}},
        {"application": "FishE", "name": "save-loaded", "tags": {"version": version}},
    ]
    assert capsys.readouterr().out == usageReporting.NOTICE + "\n"
    assert not game.usageReporting.enabled  # closed by play()


def test_quitting_at_the_save_menu_reports_startup_only(reportingOn, stub):
    def quit(self):
        self.running = False

    game = createFishE(quit)
    assert stub.waitFor(1)
    game.userInterface = MagicMock()
    game.play()

    assert not stub.waitFor(2, timeout=0.5)
    assert stub.requests[0]["body"]["name"] == "startup"


def test_the_game_starts_with_a_disabled_client_before_settings_are_read(
    monkeypatch, stub
):
    # Whatever the settings turn out to say, nothing reports before Config()
    # has been read - and with the opt-out set, nothing reports at all.
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", "false")
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENDPOINT", stub.url)

    game = createFishE(lambda self: None)

    assert not game.usageReporting.enabled
    assert not stub.waitFor(1, timeout=0.5)


def test_nothing_identifying_is_sent(reportingOn, stub):
    game = createFishE(lambda self: None)
    assert stub.waitFor(2)
    # play() with the run already over does only what every ending does:
    # release the front-end and close the client.
    game.running = False
    game.userInterface = MagicMock()
    game.play()

    for request in stub.requests:
        assert set(request["body"]) <= {"application", "name", "tags"}
        assert set(request["body"]["tags"]) == {"version"}
