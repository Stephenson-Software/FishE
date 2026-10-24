#!/usr/bin/env python3
"""Render this game's location stills from art/stills.json (RFC 0025).

    python3 art/render.py --strata-golden /path/to/strata-golden [--only KEY]
    python3 art/render.py --check          # budget and manifest only, no render

With Pillow importable (e.g. `uv run --with pillow python art/render.py ...`)
each PNG is re-encoded losslessly with zlib's best settings after it is
rendered, which roughly halves it; without Pillow the PNG is kept as Strata
wrote it and the budget check may fail.

Each still is one Strata scene file, drawn offline and headless by Strata's
own golden-image tool:

    strata-golden render <scene> <out.png> --surface headless

strata-golden ships in Strata's Linux release tarball from v0.6.0 on (bin/,
beside lib/libstrata.so, which this script puts on LD_LIBRARY_PATH). Fetch the
release stills.json names ("strata") and pass the binary here (or set
STRATA_GOLDEN):

    gh release download v0.6.0 -R Preponderous-Software/strata -p '*linux-x64*'
    mkdir strata && tar -xzf strata-0.6.0-linux-x64.tar.gz -C strata
    python3 art/render.py --strata-golden strata/bin/strata-golden

On Linux the headless surface is Mesa's EGL; llvmpipe (software) is what the
stills were rendered with and is set below unless the environment says
otherwise.

The sun is not written in the scene files. Each still's "sun" entry in the
manifest (date, local time, UTC offset, latitude, longitude) is appended to
its scene as a `sun date` line (Strata ABI 1.6) at render time, so the place
and season live in one file. Until every field of a still's sun is filled in,
this script refuses to render it rather than guess.

The rendered PNGs are committed under pictures/ and shipped inside game.zip;
CI never re-renders them (two renderers are not expected to agree byte for
byte). The total size of pictures/ is held to the manifest's budgetBytes.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

ART = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ART)
MANIFEST = os.path.join(ART, "stills.json")
PICTURES = os.path.join(ROOT, "pictures")
SUN_FIELDS = ("date", "time", "utcOffset", "latitude", "longitude")


def loadManifest(path=MANIFEST):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sunProblems(key, still):
    """Why this still's sun cannot be placed yet - empty when it can."""
    sun = still.get("sun")
    if sun is None:
        return ['%s: no "sun" entry' % key]
    missing = [field for field in SUN_FIELDS if sun.get(field) in (None, "")]
    return ["%s: sun.%s is not filled in" % (key, field) for field in missing]


def sunLine(sun):
    return "sun date %s %s %s %s %s" % (
        sun["date"],
        sun["time"],
        sun["utcOffset"],
        sun["latitude"],
        sun["longitude"],
    )


def picturesBytes(directory=PICTURES):
    if not os.path.isdir(directory):
        return 0
    return sum(
        os.path.getsize(os.path.join(directory, name))
        for name in os.listdir(directory)
        if name.endswith(".png")
    )


def checkBudget(manifest):
    used = picturesBytes()
    budget = manifest["budgetBytes"]
    print("pictures/: %d bytes of a %d-byte budget" % (used, budget))
    if used > budget:
        print("over budget by %d bytes" % (used - budget), file=sys.stderr)
        return False
    return True


def optimize(path):
    """Re-encode a PNG losslessly, smaller. The pixels do not change."""
    try:
        from PIL import Image
    except ImportError:
        print("  (Pillow not importable: %s left as rendered)" % path)
        return
    with Image.open(path) as image:
        image.load()
        pixels = image.convert("RGB")
    pixels.save(path, "PNG", optimize=True)


def render(key, still, strataGolden):
    scenePath = os.path.join(ROOT, still["scene"])
    with open(scenePath, encoding="utf-8") as f:
        scene = f.read()
    if any(line.split()[:2] == ["sun", "date"] for line in scene.splitlines()):
        raise SystemExit(
            "%s: %s has its own `sun date` line; the sun belongs in "
            "stills.json" % (key, still["scene"])
        )
    # Written beside the scene so its `include` lines resolve the same way.
    handle, temporary = tempfile.mkstemp(
        prefix=".render-%s-" % key, suffix=".scene", dir=os.path.dirname(scenePath)
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            f.write(scene.rstrip("\n") + "\n" + sunLine(still["sun"]) + "\n")
        os.makedirs(PICTURES, exist_ok=True)
        out = os.path.join(PICTURES, key + ".png")
        env = dict(os.environ)
        env.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
        env.setdefault("GALLIUM_DRIVER", "llvmpipe")
        # The release tarball's strata-golden finds libstrata.so in ../lib.
        lib = os.path.join(os.path.dirname(os.path.dirname(strataGolden)), "lib")
        if os.path.isdir(lib):
            env["LD_LIBRARY_PATH"] = os.pathsep.join(
                filter(None, [lib, env.get("LD_LIBRARY_PATH")])
            )
        subprocess.run(
            [strataGolden, "render", temporary, out, "--surface", "headless"],
            check=True,
            env=env,
        )
        optimize(out)
        print("%s -> pictures/%s.png (%d bytes)" % (key, key, os.path.getsize(out)))
    finally:
        os.remove(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--strata-golden", default=os.environ.get("STRATA_GOLDEN"))
    parser.add_argument("--only", action="append", help="render just this key")
    parser.add_argument(
        "--check", action="store_true", help="check the manifest and budget only"
    )
    args = parser.parse_args(argv)
    manifest = loadManifest()
    stills = manifest["stills"]
    keys = args.only or sorted(stills)
    unknown = [key for key in keys if key not in stills]
    if unknown:
        raise SystemExit("not in stills.json: %s" % ", ".join(unknown))

    problems = [p for key in keys for p in sunProblems(key, stills[key])]
    if problems:
        print(
            "Refusing to render: the sun cannot be placed until stills.json "
            "says where and when.",
            file=sys.stderr,
        )
        for problem in problems:
            print("  " + problem, file=sys.stderr)
        return 2

    if not args.check:
        if not args.strata_golden:
            raise SystemExit(
                "Pass --strata-golden (or set STRATA_GOLDEN) - see the top of "
                "this file for how to build it at Strata %s." % manifest["strata"]
            )
        for key in keys:
            render(key, stills[key], args.strata_golden)
    return 0 if checkBudget(manifest) else 1


if __name__ == "__main__":
    sys.exit(main())
