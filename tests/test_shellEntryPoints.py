"""Every entry point that runs the suite must run it headlessly.

The pygame front-end's tests open a real display unless SDL is pointed at its
dummy drivers, so a suite run without them fails on any machine that hasn't got
one. Three separate places run pytest - run.sh, test.sh and the CI workflow -
and only the workflow is exercised on every push, so the two shell scripts are
free to drift back out of agreement with it unnoticed. These tests assert the
agreement itself rather than any particular test's behaviour.

run.sh has the additional constraint that the drivers must be scoped to the
pytest command: it goes on to launch the game, and a dummy video driver
exported for the whole script would draw the pygame front-end to nowhere.
"""

import os

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

DUMMY_DRIVERS = ("SDL_VIDEODRIVER=dummy", "SDL_AUDIODRIVER=dummy")


def readRepositoryFile(*parts):
    with open(os.path.join(REPOSITORY_ROOT, *parts), encoding="utf-8") as repoFile:
        return repoFile.read()


def pytestCommands(script):
    """The lines of a shell script that actually invoke pytest, with comments
    dropped so a mention in prose can't stand in for the real thing."""
    commands = []
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "-m pytest" in stripped:
            commands.append(stripped)
    return commands


def assertRunsPytestHeadlessly(scriptName):
    """Every pytest invocation in the named script carries both drivers - and
    there is at least one, so a script that stopped running the suite at all
    can't pass by having nothing left to check."""
    commands = pytestCommands(readRepositoryFile(scriptName))

    assert commands, "%s no longer runs pytest" % scriptName
    for command in commands:
        for driver in DUMMY_DRIVERS:
            assert driver in command, "%s runs pytest without %s" % (
                scriptName,
                driver,
            )


def test_test_sh_runs_pytest_under_the_dummy_sdl_drivers():
    assertRunsPytestHeadlessly("test.sh")


def test_run_sh_runs_pytest_under_the_dummy_sdl_drivers():
    assertRunsPytestHeadlessly("run.sh")


def test_run_sh_does_not_leave_the_dummy_drivers_set_for_the_game():
    # prepare
    script = readRepositoryFile("run.sh")

    # call
    launchCommands = [
        line.strip()
        for line in script.splitlines()
        if "src/fishE.py" in line and not line.strip().startswith("#")
    ]

    # check
    assert launchCommands
    for command in launchCommands:
        assert "SDL_VIDEODRIVER" not in command
    assert "export SDL_" not in script


def test_ci_workflow_runs_pytest_under_the_same_dummy_sdl_drivers():
    # prepare
    workflow = readRepositoryFile(".github", "workflows", "test.yml")

    # call
    settings = [line.strip() for line in workflow.splitlines()]

    # check
    assert "SDL_VIDEODRIVER: dummy" in settings
    assert "SDL_AUDIODRIVER: dummy" in settings
