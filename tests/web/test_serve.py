import threading
import urllib.error
import urllib.request

from web.serve import _Handler, _Server


def startServer():
    server = _Server(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, port = server.server_address[0], server.server_address[1]
    return server, f"http://{host}:{port}"


def get(url):
    return urllib.request.urlopen(url, timeout=5)


def test_serves_the_game_page():
    server, base = startServer()
    try:
        response = get(base + "/")
        body = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()

    assert response.status == 200
    assert "game-worker.js" in body


def test_cross_origin_isolation_headers_are_present():
    # Without these the page is not cross-origin isolated, SharedArrayBuffer is
    # undefined, and the player's input can never reach the blocked game Worker.
    server, base = startServer()
    try:
        response = get(base + "/")
    finally:
        server.shutdown()
        server.server_close()

    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"


def test_serves_the_shared_browser_client():
    server, base = startServer()
    try:
        body = get(base + "/web/client.js").read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()

    assert "FisheClient" in body


def test_play_path_serves_the_game_page():
    server, base = startServer()
    try:
        body = get(base + "/play").read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()

    assert "game-worker.js" in body


def test_does_not_serve_the_rest_of_the_repository():
    # SimpleHTTPRequestHandler is rooted at the repository, so anything outside
    # web/ has to be refused explicitly.
    server, base = startServer()
    try:
        try:
            get(base + "/src/fishE.py")
            served = True
        except urllib.error.HTTPError as e:
            served = False
            status = e.code
    finally:
        server.shutdown()
        server.server_close()

    assert not served
    assert status == 404
