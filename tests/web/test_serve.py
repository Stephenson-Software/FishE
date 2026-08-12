import threading
import urllib.error
import urllib.request

import pytest

from web.serve import _bindServer, _Handler, _resolvePort, _Server


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


def test_port_defaults_to_the_one_the_dockerfile_sets(monkeypatch):
    monkeypatch.delenv("FISHE_WEB_PORT", raising=False)

    assert _resolvePort() == 8080


def test_port_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("FISHE_WEB_PORT", "9001")

    assert _resolvePort() == 9001


def test_misspelled_port_names_the_variable(monkeypatch):
    # This entry point is the one the Dockerfile runs, so its port is the one
    # most likely to arrive from outside - and a bare int() conversion error
    # names neither the variable nor what it should hold.
    monkeypatch.setenv("FISHE_WEB_PORT", "80801x")

    with pytest.raises(ValueError, match="FISHE_WEB_PORT"):
        _resolvePort()

    with pytest.raises(ValueError, match="80801x"):
        _resolvePort()


def test_free_port_is_bound_and_handed_back():
    server = _bindServer("127.0.0.1", 0)
    try:
        boundHost, boundPort = server.server_address[0], server.server_address[1]
    finally:
        server.server_close()

    assert boundHost == "127.0.0.1"
    assert boundPort != 0


def test_taken_port_is_explained_rather_than_traced():
    # "It is already running in another terminal" is the ordinary failure, and
    # allow_reuse_address does not cover it: that only reopens a socket left in
    # TIME_WAIT, while a live listener still refuses the bind.
    server, _ = startServer()
    host, port = server.server_address[0], server.server_address[1]
    try:
        with pytest.raises(OSError) as raised:
            _bindServer(host, port)
    finally:
        server.shutdown()
        server.server_close()

    message = str(raised.value)
    assert "FISHE_WEB_PORT" in message
    assert "already listening" in message
    assert str(port) in message
