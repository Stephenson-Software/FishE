"""web/serve.py is a thin call into tak.web.serve; these tests pin what FishE
asks of it - its page, its title in errors, its variables, its port default -
and that the kit's assets reach the browser from this repository's checkout.
The server's own behaviour is tested in tak."""

import os
import socket
import threading
import urllib.error
import urllib.request

import pytest

from tak.web import serve as kitServe

from web.serve import REPOSITORY_ROOT


@pytest.fixture
def server():
    httpd = kitServe.bindServer(REPOSITORY_ROOT, "FishE", "FISHE", "127.0.0.1", 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:%d" % httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()


def get(base, path):
    return urllib.request.urlopen(base + path, timeout=5)


@pytest.mark.parametrize("path", ["/", "/play", "/index.html"])
def test_serves_fishes_page_with_isolation_headers(server, path):
    response = get(server, path)
    body = response.read().decode("utf-8")
    assert "<title>FishE</title>" in body
    assert "fish a seaside village" in body
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"


def test_the_page_keeps_the_saves_database_name():
    # Existing players' browser saves live under this IndexedDB name; the
    # kit's boot config is where it is now set, and it must not move.
    with open(
        os.path.join(REPOSITORY_ROOT, "web", "index.html"), encoding="utf-8"
    ) as page:
        html = page.read()
    assert 'idbName: "fishe-saves"' in html
    assert 'saveDirEnv: "FISHE_SAVE_DIR"' in html
    assert 'entry: "web/pyodide_main.py"' in html


def test_the_page_credits_the_author_outside_the_game_area(server):
    body = get(server, "/").read().decode("utf-8")
    credit = '<a href="https://danielstephenson.dev">danielstephenson.dev</a>'
    assert "More by Daniel Stephenson &rarr; " + credit in body
    # After #app has closed, so the line sits below the game, not inside it.
    assert body.index(credit) > body.index('<div id="app"></div>')

def test_serves_the_kits_client_and_boot_script(server):
    assert b"window.TakClient" in get(server, "/tak/client.js").read()
    assert b"window.TakBoot" in get(server, "/tak/boot.js").read()
    assert b"loadPyodide" in get(server, "/tak/game-worker.js").read()


def test_does_not_serve_the_rest_of_the_repository(server):
    for path in ("/src/fishE.py", "/README.md", "/tak/../serve.py"):
        with pytest.raises(urllib.error.HTTPError) as error:
            get(server, path)
        assert error.value.code == 404, path


def test_port_defaults_to_the_one_the_dockerfile_sets(monkeypatch):
    monkeypatch.delenv("FISHE_WEB_PORT", raising=False)
    assert kitServe.resolvePort("FISHE") == 8080


def test_port_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("FISHE_WEB_PORT", "9090")
    assert kitServe.resolvePort("FISHE") == 9090


def test_misspelled_port_names_the_variable(monkeypatch):
    monkeypatch.setenv("FISHE_WEB_PORT", "eighty")
    with pytest.raises(ValueError) as error:
        kitServe.resolvePort("FISHE")
    assert "FISHE_WEB_PORT" in str(error.value)


def test_taken_port_is_explained_rather_than_traced():
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    try:
        with pytest.raises(OSError) as error:
            kitServe.bindServer(
                REPOSITORY_ROOT, "FishE", "FISHE", "127.0.0.1", blocker.getsockname()[1]
            )
    finally:
        blocker.close()
    assert "FishE" in str(error.value) and "FISHE_WEB_PORT" in str(error.value)
