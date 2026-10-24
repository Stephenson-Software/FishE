"""The Dockerfile must install the same tak that everything else is tested on.

tak is pinned to a commit twice. requirements.txt is what CI, run.sh and the
README's Setup step install, so it is the version the suite runs against. The
Dockerfile installs tak on its own line instead - deliberately, since the image
needs nothing else from requirements.txt - and web/build_zip.py copies that
install into the bundle the browser plays. Only requirements.txt is exercised
on every push, so a bump there that missed the Dockerfile would leave CI green
while the deployed game ran on a tak the suite never saw. These tests assert
the agreement itself.
"""

import os
import re

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

TAK_REQUIREMENT = re.compile(r"tak @ git\+\S+?@[0-9a-f]+")


def readRepositoryFile(*parts):
    with open(os.path.join(REPOSITORY_ROOT, *parts), encoding="utf-8") as repoFile:
        return repoFile.read()


def takRequirements(text):
    """Every tak requirement named in the file, with comments dropped so a
    mention in prose can't stand in for the real thing."""
    requirements = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        requirements += TAK_REQUIREMENT.findall(line)
    return requirements


def test_requirements_pin_tak_exactly_once():
    assert len(takRequirements(readRepositoryFile("requirements.txt"))) == 1


def test_dockerfile_installs_the_tak_pinned_in_requirements():
    # prepare
    pinned = takRequirements(readRepositoryFile("requirements.txt"))

    # call
    installed = takRequirements(readRepositoryFile("Dockerfile"))

    # check
    assert installed, "the Dockerfile no longer installs tak"
    assert installed == pinned


def test_tak_requirement_finds_a_pin_and_ignores_comments():
    # prepare
    text = (
        "# tak @ git+https://github.com/Stephenson-Software/tak@aaaaaaa\n"
        'RUN pip install "tak @ git+https://github.com/Stephenson-Software/tak@bbbbbbb" \\\n'
    )

    # call
    requirements = takRequirements(text)

    # check
    assert requirements == [
        "tak @ git+https://github.com/Stephenson-Software/tak@bbbbbbb"
    ]
