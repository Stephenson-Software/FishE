import os
import zipfile

from web.build_zip import build

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def buildBundle(tmp_path, monkeypatch):
    # The bundle stores repo-relative paths, so it has to be built from the
    # repository root - that is what makes the unpacked tree in the browser
    # match a checkout.
    monkeypatch.chdir(REPOSITORY_ROOT)
    outputPath = tmp_path / "game.zip"
    build(outputPath=str(outputPath))
    with zipfile.ZipFile(outputPath) as bundle:
        return bundle.namelist()


def test_bundle_carries_the_game(tmp_path, monkeypatch):
    names = buildBundle(tmp_path, monkeypatch)

    assert os.path.join("src", "fishE.py") in names
    assert os.path.join("src", "ui", "pyodideUserInterface.py") in names
    assert os.path.join("src", "browserSaveSync.py") in names


def test_bundle_carries_the_schemas_the_save_readers_validate_against(
    tmp_path, monkeypatch
):
    # The *JsonReaderWriter modules resolve these paths relative to the cwd the
    # Worker chdir's into, so a bundle without them fails every save load.
    names = buildBundle(tmp_path, monkeypatch)

    for schema in ("player.json", "stats.json", "timeService.json"):
        assert os.path.join("schemas", schema) in names


def test_bundle_carries_the_worker_entry_point(tmp_path, monkeypatch):
    names = buildBundle(tmp_path, monkeypatch)

    assert os.path.join("web", "pyodide_main.py") in names


def test_bundle_carries_the_shared_browser_client(tmp_path, monkeypatch):
    # The page fetches these over HTTP, so the browser does not need them from
    # the bundle - but webUserInterface reads them from the filesystem, and the
    # Pyodide front-end subclasses it. Shipping them means that read can never
    # be the thing that fails inside the Worker.
    names = buildBundle(tmp_path, monkeypatch)

    assert os.path.join("web", "client.js") in names
    assert os.path.join("web", "client.css") in names


def test_bundle_excludes_build_artifacts(tmp_path, monkeypatch):
    names = buildBundle(tmp_path, monkeypatch)

    assert not [name for name in names if "__pycache__" in name]
    assert not [name for name in names if name.endswith(".pyc")]
