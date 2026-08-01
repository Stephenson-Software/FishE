"""Both web front-ends must render from the same browser client.

FishE has three front-ends behind one contract, and the two browser ones are
the easiest pair to let drift: a screen type handled in the server-backed page
but not in the Pyodide one looks fine in local testing and blank in production.
Neither front-end owning its own copy of the renderer is what prevents that, so
these tests assert the sharing itself rather than any particular screen.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ui import webUserInterface  # noqa: E402

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEB_DIRECTORY = os.path.join(REPOSITORY_ROOT, "web")


def readWebFile(name):
    with open(os.path.join(WEB_DIRECTORY, name), encoding="utf-8") as webFile:
        return webFile.read()


def test_server_backed_page_inlines_the_shared_client():
    page = webUserInterface.HTML_PAGE

    assert readWebFile("client.js") in page
    assert readWebFile("client.css") in page


def test_pyodide_page_links_the_shared_client():
    page = readWebFile("index.html")

    assert "/web/client.js" in page
    assert "/web/client.css" in page


def test_both_front_ends_hand_the_client_a_transport():
    # FisheClient.init(sendFn) is the seam: the renderer is shared, how a
    # response gets back to the game is not.
    assert "FisheClient.init(" in webUserInterface.HTML_PAGE
    assert "FisheClient.init(" in readWebFile("index.html")


def test_a_missing_client_file_explains_where_it_should_be():
    try:
        webUserInterface._readWebAsset("no-such-client.js")
        raised = None
    except RuntimeError as e:
        raised = e

    assert raised is not None
    message = str(raised)
    assert "web/" in message
    assert "no-such-client.js" in message
