# @author Daniel McCoy Stephenson
"""Usage reporting: tell the trace service that FishE was started.

FishE reports two events to https://trace.danielstephenson.dev through the
vendored trace client (src/trace_client.py): ``startup`` once per launch and
``save-loaded`` each time a save slot is created or opened. Each carries the
program name, the version from version.txt and a random installation ID (the
tag ``install``, so installations can be counted rather than launches), and
nothing else - no username, hostname, address, path, slot number or anything
about the run. The ID is a UUID the client keeps in ``trace-install-id`` in the
save directory (``TRACE_INSTALL_ID`` in the environment pins one instead); the
client only reads or creates it when reporting is on.

Reporting is on by default and switched off with
``FISHE_USAGE_REPORTING_ENABLED=false`` in the environment (see
config.Config), or with the two variables every trace client honours,
``TRACE_USAGE_REPORTING=off`` and ``DO_NOT_TRACK=1``. Those two are checked by
the client itself, in its constructor, before FishE's own setting - so they
win even when the setting says on. The first time an install reports, one
line saying so is printed on the console and a marker file is left in the
save directory so it is not printed again. What is sent and how to turn it
off is written up at https://danielstephenson.dev/usage-reporting.

The client never gets in the game's way: every report returns immediately (the
HTTP call happens on a daemon thread the client owns), never raises, and at
most 256 reports are queued before new ones are dropped. A disabled client
does nothing and starts no thread.

Under Pyodide (the in-browser front-end) there are no OS threads or sockets, so
the browser build never builds an enabled client; only the console, pygame and
server-backed web front-ends report.
"""

import os
import sys

from trace_client import TraceClient

# The name the trace service issued FishE's key for. It is the `application`
# value on every event and must not change without a new key.
PROGRAM_NAME = "FishE"

# Written into the save directory once the first-run notice has been shown.
# Its contents are the notice itself, so anyone finding the file knows what it
# is. SaveFileManager ignores it: only slot_N directories are save slots.
NOTICE_MARKER_FILENAME = "usage-reporting-notice-shown"

# The file in the save directory the client keeps this installation's random
# ID in (the tag ``install`` on every event). Deleting it resets the ID; like
# the marker, SaveFileManager does not read it as a save slot.
INSTALL_ID_FILENAME = "trace-install-id"

OPT_OUT_INSTRUCTION = (
    "FISHE_USAGE_REPORTING_ENABLED=false or TRACE_USAGE_REPORTING=off "
    "in the environment"
)

DETAILS_URL = "https://danielstephenson.dev/usage-reporting"

NOTICE = (
    "Usage reporting is on: %s sends a startup event and a save-loaded event "
    "(program name, version and a random installation ID only) to "
    "trace.danielstephenson.dev. "
    "Turn it off with %s. Details: %s"
    % (PROGRAM_NAME, OPT_OUT_INSTRUCTION, DETAILS_URL)
)

VERSION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "version.txt"
)


def isBrowserBuild():
    """True inside Pyodide, where the client's sending thread cannot start."""
    return sys.platform == "emscripten"


def readVersion(path=None):
    """The version from version.txt (the one run.sh prints), or None."""
    try:
        with open(path or VERSION_FILE, encoding="utf-8") as versionFile:
            version = versionFile.read().strip()
    except (IOError, OSError, UnicodeDecodeError):
        return None
    return version or None


def programVersion():
    """The version the client tags every event with: version.txt's, or
    "unknown" when it cannot be read, so a missing file never stops the game
    from starting (the client refuses a blank version)."""
    return readVersion() or "unknown"


def createClient(config):
    """Build the client the settings in config ask for.

    The browser build yields TraceClient.disabled() outright. Everything else
    goes through the client's constructor, which decides in this order:
    TRACE_USAGE_REPORTING / DO_NOT_TRACK in the environment, then FishE's own
    setting, then whether there is a key. A client switched off by any of
    them reports nothing, starts no thread, and says why in disabled_reason.

    Only an enabled client resolves the installation ID: TRACE_INSTALL_ID
    when set, otherwise the file at installIdPath(config), created on first
    use - so no opt-out ever creates it."""
    if isBrowserBuild():
        return TraceClient.disabled()
    return TraceClient(
        config.usageReportingEndpoint,
        PROGRAM_NAME,
        programVersion(),
        key=config.usageReportingKey,
        enabled=config.usageReportingEnabled,
        install_id=os.environ.get("TRACE_INSTALL_ID"),
        install_id_file=installIdPath(config),
    )


def installIdPath(config):
    return os.path.join(config.dataDirectory, INSTALL_ID_FILENAME)


def noticeMarkerPath(config):
    return os.path.join(config.dataDirectory, NOTICE_MARKER_FILENAME)


def showNoticeOnce(config, output=None):
    """Print the first-run notice unless the marker says it has been shown.

    Printed rather than shown through the front-end: this is a line for the
    person who launched the program, alongside run.sh's version line and the
    web front-end's URL, not a screen in the game. Returns True on the call
    that printed it.

    The marker is written into the save directory, which is the one place
    FishE already keeps state between runs. If it cannot be written the
    notice is still printed - being told twice is the lesser failure."""
    markerPath = noticeMarkerPath(config)
    if os.path.exists(markerPath):
        return False
    print(NOTICE, file=output if output is not None else sys.stdout)
    try:
        os.makedirs(config.dataDirectory, exist_ok=True)
        with open(markerPath, "w", encoding="utf-8") as marker:
            marker.write(NOTICE + "\n")
    except (IOError, OSError):
        pass
    return True


def start(config, output=None):
    """Build the client, say so the first time, and report startup.

    Returns the client (possibly disabled) for the game to keep: it reports
    save-loaded through it and closes it when the run ends."""
    client = createClient(config)
    if client.enabled:
        showNoticeOnce(config, output)
        client.report("startup")
    return client
