import os
import sys
import textwrap

from src.browserSaveSync import getJsModule, syncBrowserSaves


class FakeJs:
    def __init__(self, raises=None):
        self.callCount = 0
        self.raises = raises

    def syncSaves(self):
        self.callCount += 1
        if self.raises is not None:
            raise self.raises


def installFakeJs(js):
    previous = sys.modules.get("js")
    sys.modules["js"] = js
    return previous


def restoreJs(previous):
    if previous is None:
        sys.modules.pop("js", None)
    else:
        sys.modules["js"] = previous


def test_finds_js_when_it_is_importable_but_not_yet_imported(tmp_path, monkeypatch):
    """Regression: this is exactly the state Pyodide starts the game in.

    `js` is importable under Pyodide but is not in sys.modules until something
    imports it. Looking only in sys.modules therefore reported "not a browser"
    while running in one — which stopped the Pyodide front-end from starting
    at all, and would have turned every save into a silent no-op.
    """
    jsModule = tmp_path / "js.py"
    jsModule.write_text(
        textwrap.dedent(
            """
        calls = []

        def syncSaves():
            calls.append(1)
    """
        )
    )
    monkeypatch.syspath_prepend(os.fspath(tmp_path))
    monkeypatch.delitem(sys.modules, "js", raising=False)

    try:
        assert getJsModule() is not None
        assert syncBrowserSaves() is True
        assert sys.modules["js"].calls == [1]
    finally:
        sys.modules.pop("js", None)


def test_no_op_outside_a_browser():
    # No `js` module: the console, pygame and server-backed web front-ends all
    # write real files, so there is nothing to flush anywhere.
    previous = sys.modules.pop("js", None)
    try:
        assert syncBrowserSaves() is False
    finally:
        restoreJs(previous)


def test_no_op_when_the_worker_did_not_install_syncSaves():
    class JsWithoutSyncSaves:
        pass

    previous = installFakeJs(JsWithoutSyncSaves())
    try:
        assert syncBrowserSaves() is False
    finally:
        restoreJs(previous)


def test_flushes_through_the_worker_hook():
    js = FakeJs()
    previous = installFakeJs(js)
    try:
        assert syncBrowserSaves() is True
    finally:
        restoreJs(previous)
    assert js.callCount == 1


def test_a_browser_that_refuses_to_store_does_not_end_the_game(capsys):
    js = FakeJs(raises=RuntimeError("QuotaExceededError"))
    previous = installFakeJs(js)
    try:
        assert syncBrowserSaves() is False
    finally:
        restoreJs(previous)

    # The player is told what happened, what it means for their progress, and
    # what to check - not just handed the exception text.
    output = capsys.readouterr().out
    assert "QuotaExceededError" in output
    assert "browser storage" in output
    assert "private" in output
