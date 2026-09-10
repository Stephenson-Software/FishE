# /bin/bash
# Usage: ./test.sh

# The pygame front-end's tests open a real display unless SDL is pointed at its
# dummy drivers, so without these the suite fails on any machine that hasn't got
# one - a container, an SSH session, WSL without an X server. The CI workflow
# sets the same two (see .github/workflows/test.yml); they belong here so a run
# off a developer's machine agrees with the one on the pull request.
#
# Scoped to this one command rather than exported, to match run.sh, where the
# game is launched afterwards and must not inherit a dummy video driver.

# generate coverage file named "cov.xml"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest --verbose -vv --cov=src --cov-report=term-missing --cov-report=xml:cov.xml
