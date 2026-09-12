import os

# Usage reporting (see src/usageReporting.py). The key is the program key the
# trace service issued to FishE; it identifies the program, not the player,
# and is bundled so an install that never sets FISHE_USAGE_REPORTING_KEY still
# reports.
USAGE_REPORTING_ENDPOINT_DEFAULT = "https://trace.danielstephenson.dev"
USAGE_REPORTING_KEY_DEFAULT = "_zbWO4qi0bhg9RoKxYXCCy93D36R5dF0Sa5xCiR180E"

# Values that switch a FISHE_* boolean off. Anything else - including unset
# and empty - leaves the default in place, matching FISHE_SAVE_DIR above.
_FALSE_VALUES = ("0", "false", "no", "off")


def _environmentFlag(name, default):
    """Read a boolean FISHE_* variable, falling back to default when it is
    unset or empty so a compose file with `NAME=` doesn't flip the switch."""
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    return value not in _FALSE_VALUES


# @author Daniel McCoy Stephenson
class Config:
    def __init__(self):
        # Save file paths. FISHE_SAVE_DIR relocates the whole save directory,
        # which deployments use to point the game somewhere other than a
        # cwd-relative "data" — a mounted volume for a server install, or the
        # Worker-side directory that the Pyodide front-end mirrors to the
        # browser's IndexedDB (see browserSaveSync and web/game-worker.js).
        self.dataDirectory = os.environ.get("FISHE_SAVE_DIR") or "data"

        # Initial player values. Starting energy isn't configured here - see
        # player.py, which sources it from the housing ladder instead.
        self.initialMoney = 20
        self.initialFishCount = 0
        self.initialMoneyInBank = 0.01
        self.initialFishMultiplier = 1
        self.initialPriceForBait = 50

        # Usage reporting: one startup event (and one when a save is opened)
        # to the trace service, program name and version only. On by default;
        # FISHE_USAGE_REPORTING_ENABLED=false is the opt-out. The endpoint and
        # key overrides exist so a self-hosted trace can be pointed at, and so
        # tests can aim the client at a loopback stub instead of production.
        self.usageReportingEnabled = _environmentFlag(
            "FISHE_USAGE_REPORTING_ENABLED", True
        )
        self.usageReportingEndpoint = (
            os.environ.get("FISHE_USAGE_REPORTING_ENDPOINT", "").strip()
            or USAGE_REPORTING_ENDPOINT_DEFAULT
        )
        self.usageReportingKey = (
            os.environ.get("FISHE_USAGE_REPORTING_KEY", "").strip()
            or USAGE_REPORTING_KEY_DEFAULT
        )
