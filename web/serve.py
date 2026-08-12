# @author Daniel McCoy Stephenson
"""Static file server for the browser-native (Pyodide) build of FishE.

Unlike examples/web_app.py, this server does not run the game — it only hands
the browser the files it needs, and the game then runs in the player's own tab
with its saves in that browser's IndexedDB. Every visitor gets their own game
and their own save slots, and the server keeps no state at all.

    python3 web/serve.py        # then open the URL it prints

Routes:
  /  /play  /play/  /index.html  → web/index.html
  /web/...                       → the web/ directory (game.zip, worker, client)
  everything else                → 404

The Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy headers below are
not optional: without them the page is not cross-origin isolated, and
SharedArrayBuffer — which is how the player's input reaches the blocked game
Worker — is not available at all. web/index.html says so on screen if they are
missing, which is the usual symptom of a proxy in front of this server dropping
them.
"""

import errno
import http.server
import os
from urllib.parse import unquote, urlparse

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

INDEX_PATHS = ("/", "/play", "/play/", "/index.html")

# FISHE_WEB_PORT is read here and by UserInterfaceFactory's WEB branch, with a
# different default in each: 8080 for this server (what the Dockerfile sets),
# 8000 for the server-backed front-end behind examples/web_app.py. They are
# separate programs that can be run at the same time, so the defaults are
# deliberately not shared - the check on the value is, so a misspelled port
# names itself whichever one the player started.
DEFAULT_PORT = "8080"


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPOSITORY_ROOT, **kwargs)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in INDEX_PATHS:
            self._sendIndex()
            return
        if not path.startswith("/web/"):
            self.send_error(404, "Not found")
            return
        super().do_GET()

    def _sendIndex(self):
        indexPath = os.path.join(WEB_DIRECTORY, "index.html")
        try:
            with open(indexPath, "rb") as indexFile:
                body = indexFile.read()
        except OSError as e:
            self.send_error(
                500,
                "FishE's page is missing",
                f"Could not read {indexPath}: {e}. That file ships in the "
                f"repository's web/ directory — serve the game from a complete "
                f"checkout.",
            )
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Required for SharedArrayBuffer, which the Pyodide front-end uses to
        # deliver input to the (blocked) game Worker.
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    def log_message(self, *args):
        pass  # keep the container's logs to what the game itself says


class _Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def _resolvePort():
    """The port to serve on, or a ValueError naming the variable that is wrong."""
    portText = os.environ.get("FISHE_WEB_PORT", DEFAULT_PORT)
    try:
        return int(portText)
    except ValueError:
        raise ValueError(f"FISHE_WEB_PORT must be an integer, got: {portText!r}")


def _bindServer(host, port):
    """Bind the server, turning a refused address into a sentence.

    A port that is already listening - a second copy of the game, most often -
    otherwise surfaces as an errno raised from inside http.server, naming
    neither FishE nor the variable the player would have to change."""
    try:
        return _Server((host, port), _Handler)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            reason = "something else is already listening there"
        elif e.errno == errno.EACCES:
            reason = "this process is not allowed to use that port"
        else:
            reason = str(e)
        raise OSError(
            f"FishE could not be served at http://{host}:{port}/: {reason}. "
            f"Set FISHE_WEB_PORT to a free port (or FISHE_WEB_HOST to an "
            f"address this machine can bind) and start it again."
        ) from e


def main():
    host = os.environ.get("FISHE_WEB_HOST", "127.0.0.1")
    port = _resolvePort()
    # Bound before the URL is announced, so a failure is never preceded by an
    # address that was never served.
    server = _bindServer(host, port)
    print(f"FishE is being served at http://{host}:{port}/")
    print("Open that URL to play. Press Ctrl+C here to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
