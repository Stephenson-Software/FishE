"""install.sh must run unattended, and must survive being run a second time.

The script needs root and changes /usr/games and /bin, so neither CI nor a
contributor's test run can execute it. These tests assert its contract from the
text instead: a shell to run it under, stopping at the first failure, no step
that waits on a prompt, and an existing install updated rather than cloned over.
"""

import os

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def readInstallScript():
    with open(os.path.join(REPOSITORY_ROOT, "install.sh"), encoding="utf-8") as script:
        return script.read()


def commandLines(script):
    """The lines of the script that run something, with comments and blank
    lines dropped so a mention in prose can't stand in for the real thing."""
    commands = []
    for line in script.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            commands.append(stripped)
    return commands


def test_install_sh_names_its_shell():
    # prepare
    script = readInstallScript()

    # call
    firstLine = script.splitlines()[0]

    # check
    assert firstLine == "#!/bin/sh"


def test_install_sh_stops_at_the_first_failure():
    # prepare
    script = readInstallScript()

    # call
    commands = commandLines(script)

    # check
    assert "set -e" in commands
    # before anything that installs or writes, so a failed step can't leave
    # /bin/fishe pointing at a directory that was never cloned
    assert commands.index("set -e") < min(
        index for index, command in enumerate(commands) if "apt-get" in command
    )


def test_install_sh_does_not_fail_on_an_existing_games_directory():
    # prepare
    script = readInstallScript()

    # call
    mkdirCommands = [
        command for command in commandLines(script) if command.startswith("mkdir")
    ]

    # check
    assert mkdirCommands
    for command in mkdirCommands:
        assert command.startswith("mkdir -p ")


def test_install_sh_does_not_wait_on_an_apt_prompt():
    # prepare
    script = readInstallScript()

    # call
    installCommands = [
        command for command in commandLines(script) if "apt-get install" in command
    ]

    # check
    assert installCommands
    for command in installCommands:
        assert " -y " in command


def test_install_sh_updates_an_existing_install_instead_of_cloning_over_it():
    # prepare
    script = readInstallScript()

    # call
    commands = commandLines(script)
    cloneLine = next(
        index for index, command in enumerate(commands) if "git clone" in command
    )

    # check
    assert 'if [ -d "$INSTALL_DIR/.git" ]; then' in commands[:cloneLine]
    assert 'git -C "$INSTALL_DIR" pull' in commands[:cloneLine]
    assert commands[cloneLine - 1] == "else"
