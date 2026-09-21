# @author Daniel McCoy Stephenson
"""The server-backed browser front-end: the game runs here, the browser is a
terminal for it. The server, the rendezvous and every screen now live in tak
(tak.ui.web.WebUserInterface); this module is FishE's adapter - the
(currentPrompt, timeService, player) constructor, FishE's page copy, and the
FISHE_WEB_HOST / FISHE_WEB_PORT variables.
"""

from tak.ui import web as kitWeb
from tak.ui.web import DEFAULT_HOST, DEFAULT_PORT  # noqa: F401 - re-exported
from tak.ui.web import ENDED_SCREEN_DELIVERY_TIMEOUT_SECONDS

from ui.baseUserInterface import BaseUserInterface

TITLE = "FishE"
TAGLINE = "fish a seaside village and build a fortune of $10,000"
TIP = "Tip: click an option or press its number key (1-9). Enter or Space continues."
ENV_PREFIX = "FISHE"


def resolveAddressFromEnvironment():
    """The (host, port) to serve on, from FISHE_WEB_HOST / FISHE_WEB_PORT, or a
    ValueError naming the variable that is wrong."""
    return kitWeb.resolveAddressFromEnvironment(ENV_PREFIX)


def htmlPage():
    """The single-page client with FishE's heading, built on first use."""
    return kitWeb.htmlPage(TITLE, TAGLINE, TIP)


def __getattr__(name):
    """Keep HTML_PAGE readable as a module attribute."""
    if name == "HTML_PAGE":
        return htmlPage()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class WebUserInterface(BaseUserInterface, kitWeb.WebUserInterface):
    def __init__(
        self,
        currentPrompt,
        timeService,
        player,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        start_server=True,
        endedScreenTimeoutSeconds=ENDED_SCREEN_DELIVERY_TIMEOUT_SECONDS,
    ):
        super().__init__(
            currentPrompt,
            timeService,
            player,
            title=TITLE,
            tagline=TAGLINE,
            tip=TIP,
            envPrefix=ENV_PREFIX,
            host=host,
            port=port,
            start_server=start_server,
            endedScreenTimeoutSeconds=endedScreenTimeoutSeconds,
        )
