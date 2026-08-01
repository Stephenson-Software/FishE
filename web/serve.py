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

import http.server
import os
from urllib.parse import unquote, urlparse

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

INDEX_PATHS = ("/", "/play", "/play/", "/index.html")


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


def main():
    host = os.environ.get("FISHE_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("FISHE_WEB_PORT", "8080"))
    print(f"FishE is being served at http://{host}:{port}/")
    print("Open that URL to play. Press Ctrl+C here to stop.")
    _Server((host, port), _Handler).serve_forever()


if __name__ == "__main__":
    main()
