#!/usr/bin/env python3
"""Write art/home-*.scene: one home still per rung of the housing ladder.

    python3 art/gen_homes.py          # write the five scenes
    python3 art/gen_homes.py --check  # fail if a committed scene is stale

FishE's home is wherever the player lives (src/housing/housing.py), so home
has one still per rung that has a roof - the rented room, the driftwood
shack, the cozy cottage, the sturdy cabin and the waterfront manor - and each
is drawn better than the one below it: more room, better walls and floor,
more furniture, more light, and more fishing gear, the pole being polished on
the table growing with it. A homeless player has no still.

Every home is drawn as the other interiors are (art/_room.scene): a cutaway
seen from the south-east with its roof and two near walls taken away, at
13:00 on the stills' day. They are placed in the one village: the rented room
is upstairs over the tavern, the shack stands on the shingle, the cottage and
the cabin have their gardens, and the manor stands on the harbour wall with
the water along its east side and its own jetty.

Items are axis-aligned (Strata scene items have no rotation), so planks, logs
and panels are written as rows of boxes. The output is deterministic and is
committed alongside this script; re-run after editing.
"""

import os
import sys

ART = os.path.dirname(os.path.abspath(__file__))

# The camera every interior uses for a 7 m x 6 m room (art/_room.scene).
EYE = (5.0, 4.4, 5.4)
TARGET = (-0.5, 0.7, -0.9)
FOV = 50


def fmt(v):
    text = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def rgb(c):
    return " ".join(fmt(v) for v in c)


class Scene:
    def __init__(self, header):
        self.lines = ["# " + line if line else "#" for line in header.splitlines()]

    def raw(self, line):
        self.lines.append(line)

    def note(self, text):
        self.lines.append("# " + text)

    def box(self, x, y, z, sx, sy, sz, c, alpha=None):
        line = "item cube %s %s %s  %s %s %s  %s" % (
            fmt(x),
            fmt(y),
            fmt(z),
            fmt(sx),
            fmt(sy),
            fmt(sz),
            rgb(c),
        )
        if alpha is not None:
            line += " " + fmt(alpha)
        self.lines.append(line)

    def span(self, x0, y0, z0, x1, y1, z1, c, alpha=None):
        """A box from one corner to the other."""
        self.box(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            (z0 + z1) / 2,
            abs(x1 - x0),
            abs(y1 - y0),
            abs(z1 - z0),
            c,
            alpha,
        )

    def cyl(self, x, y, z, d, h, c, dz=None):
        self.lines.append(
            "item cylinder %s %s %s  %s %s %s  %s"
            % (
                fmt(x),
                fmt(y),
                fmt(z),
                fmt(d),
                fmt(h),
                fmt(d if dz is None else dz),
                rgb(c),
            )
        )

    def ball(self, x, y, z, d, c):
        self.lines.append(
            "item sphere %s %s %s  %s %s %s  %s"
            % (fmt(x), fmt(y), fmt(z), fmt(d), fmt(d), fmt(d), rgb(c))
        )

    def light(self, x, y, z, rng, c, intensity, shadow=False):
        self.lines.append(
            "light point %s %s %s  %s  %s  %s%s"
            % (
                fmt(x),
                fmt(y),
                fmt(z),
                fmt(rng),
                rgb(c),
                fmt(intensity),
                " shadow" if shadow else "",
            )
        )

    def text(self):
        return "\n".join(self.lines) + "\n"


def camera(scene, scale, lift=0.0, shift=(0.0, 0.0, 0.0)):
    eye = [EYE[i] * scale + shift[i] for i in range(3)]
    target = [TARGET[i] * scale + shift[i] for i in range(3)]
    eye[1] += lift
    target[1] += lift
    scene.raw("size 640 360")
    scene.raw(
        "camera %s  %s  %d 0.1 300"
        % (" ".join(fmt(v) for v in eye), " ".join(fmt(v) for v in target), FOV)
    )
    scene.raw("lighting sun 0.5 54 4 2048 %s 0.6 1" % fmt(30 * scale + 10))
    scene.raw("clear 0 0 0 1 sky")


def shell(s, W, D, H, base, floor, wall, trim, cut, wallLeft=None):
    """The cutaway: floor, the back (north) and left (west) walls with a beam
    along their tops, and the cut stubs of the two missing walls."""
    hw, hd = W / 2, D / 2
    s.span(-hw, base, -hd, hw, base + 0.1, hd, floor)
    s.span(-hw - 0.2, base, -hd - 0.2, hw + 0.2, base + H, -hd, wall)
    s.span(-hw - 0.2, base, -hd, -hw, base + H, hd + 0.2, wallLeft or wall)
    s.span(
        -hw - 0.25, base + H, -hd - 0.25, hw + 0.25, base + H + 0.12, -hd + 0.05, trim
    )
    s.span(-hw - 0.25, base + H, -hd, -hw + 0.05, base + H + 0.12, hd + 0.25, trim)
    s.span(hw, base, -hd, hw + 0.2, base + 0.3, hd + 0.2, cut)
    s.span(-hw, base, hd, hw, base + 0.3, hd + 0.2, cut)


def backWindow(s, x, y, w, h, z, frame, sill=True):
    s.box(x, y, z + 0.01, w, h, 0.04, (0.75, 0.88, 0.95))
    s.box(x, y, z + 0.04, 0.06, h, 0.04, frame)
    s.box(x, y, z + 0.04, w, 0.06, 0.04, frame)
    s.box(x, y + h / 2, z + 0.04, w + 0.1, 0.08, 0.05, frame)
    if sill:
        s.box(x, y - h / 2 - 0.03, z + 0.12, w + 0.2, 0.05, 0.25, frame)


def leftWindow(s, z, y, w, h, x, frame):
    s.box(x + 0.01, y, z, 0.04, h, w, (0.75, 0.88, 0.95))
    s.box(x + 0.04, y, z, 0.04, h, 0.06, frame)
    s.box(x + 0.04, y, z, 0.04, 0.06, w, frame)
    s.box(x + 0.04, y + h / 2, z, 0.05, 0.08, w + 0.1, frame)
    s.box(x + 0.12, y - h / 2 - 0.03, z, 0.25, 0.05, w + 0.2, frame)


def table(s, x, y, z, w, d, h, top, legs, leg=0.06):
    s.box(x, y + h - 0.025, z, w, 0.05, d, top)
    for dx in (-1, 1):
        for dz in (-1, 1):
            s.box(
                x + dx * (w / 2 - leg),
                y + (h - 0.05) / 2,
                z + dz * (d / 2 - leg),
                leg,
                h - 0.05,
                leg,
                legs,
            )


def chair(s, x, y, z, c, back="-x"):
    table(s, x, y, z, 0.42, 0.42, 0.45, c, c, 0.05)
    if back == "-x":
        s.box(x - 0.19, y + 0.75, z, 0.05, 0.6, 0.42, c)
    elif back == "+x":
        s.box(x + 0.19, y + 0.75, z, 0.05, 0.6, 0.42, c)
    elif back == "-z":
        s.box(x, y + 0.75, z - 0.19, 0.42, 0.6, 0.05, c)
    else:
        s.box(x, y + 0.75, z + 0.19, 0.42, 0.6, 0.05, c)


def poleFlat(s, x, y, z, length, rod, reel, grip=(0.25, 0.18, 0.12)):
    """A rod lying along x on a surface whose top is y, with its reel."""
    s.box(x, y + 0.0125, z, length, 0.025, 0.025, rod)
    s.box(x + length / 2 - length * 0.12, y + 0.02, z, length * 0.22, 0.04, 0.04, grip)
    if reel is not None:
        s.cyl(x + length / 2 - length * 0.28, y + 0.04, z, 0.08, 0.05, reel)


def poleStanding(s, x, y, z, length, rod, reel, grip=(0.25, 0.18, 0.12)):
    """A rod standing on end (leaning in a rack or a corner)."""
    s.box(x, y + length / 2, z, 0.03, length, 0.03, rod)
    s.box(x, y + 0.22, z, 0.045, 0.44, 0.045, grip)
    if reel is not None:
        s.cyl(x + 0.04, y + 0.55, z, 0.07, 0.07, reel)


def rag(s, x, y, z, c=(0.80, 0.78, 0.70)):
    s.box(x, y + 0.015, z, 0.25, 0.03, 0.18, c)


def bed(
    s,
    x,
    y,
    z,
    w,
    length,
    frame,
    sheet,
    blanket,
    pillow,
    height=0.45,
    head=0.9,
    foot=0.5,
    posts=None,
):
    """A bed with its head against the back (north) wall, length along z."""
    z0, z1 = z - length / 2, z + length / 2
    s.box(x, y + height - 0.1, z, w, 0.12, length, frame)
    s.box(x, y + head / 2, z0 + 0.04, w + 0.06, head, 0.08, frame)
    s.box(x, y + foot / 2, z1 - 0.04, w + 0.06, foot, 0.08, frame)
    s.box(x, y + height + 0.05, z, w - 0.06, 0.18, length - 0.12, sheet)
    s.box(
        x, y + height + 0.16, z + length * 0.12, w - 0.02, 0.06, length * 0.7, blanket
    )
    for px in ((x,) if w < 1.3 else (x - w / 4, x + w / 4)):
        s.box(px, y + height + 0.2, z0 + 0.32, min(0.6, w * 0.4), 0.14, 0.34, pillow)
    if posts:
        ph, canopy = posts
        for dx in (-1, 1):
            for pz in (z0 + 0.05, z1 - 0.05):
                s.box(x + dx * (w / 2 + 0.03), y + ph / 2, pz, 0.1, ph, 0.1, frame)
        s.box(x, y + ph + 0.05, z, w + 0.2, 0.1, length + 0.1, canopy)
        s.box(x - w / 2 - 0.05, y + ph - 0.35, z, 0.04, 0.6, length + 0.1, canopy)
        s.box(x + w / 2 + 0.05, y + ph - 0.35, z, 0.04, 0.6, length + 0.1, canopy)


def rug(s, x, y, z, w, d, c, border):
    s.box(x, y + 0.005, z, w, 0.01, d, border)
    s.box(x, y + 0.008, z, w - 0.2, 0.012, d - 0.2, c)


# ---------------------------------------------------------------------------
# The rungs. Shared colours.
WOOD = (0.50, 0.36, 0.22)
DARK_WOOD = (0.36, 0.24, 0.14)
GRASS = (0.30, 0.46, 0.22)
CANE = (0.78, 0.68, 0.42)
STEEL = (0.62, 0.63, 0.66)
BRASS = (0.80, 0.62, 0.25)
WATER = (0.16, 0.34, 0.44)
STONE = (0.52, 0.50, 0.46)


def rentedRoom():
    s = Scene(
        "FishE - home on the second rung: a rented room, upstairs over the\n"
        "tavern. Small, plastered and bare: a narrow bunk, a rickety table and\n"
        "a stool, a washstand, one cheap cane pole being polished. 13:00.\n"
        "Generated by art/gen_homes.py - edit that and re-run, not this.\n"
        "Provisional art (RFC 0025): see stills.json."
    )
    W, D, H, B = 4.6, 4.0, 2.5, 3.0  # B: the floor is a storey up
    hw, hd = W / 2, D / 2
    camera(s, 0.68, lift=B, shift=(0.1, 0, 0.1))
    s.note("the street and the tavern's ground floor below the room")
    s.box(0, -0.3, 0, 60, 0.6, 60, GRASS)
    s.box(0, 0.01, 1.0, 14, 0.04, 12, (0.46, 0.44, 0.42))
    s.span(-hw - 0.2, 0, -hd - 0.2, hw + 0.2, B, hd + 0.2, (0.42, 0.40, 0.37))
    s.span(-hw - 0.25, B - 0.12, -hd - 0.25, hw + 0.25, B, hd + 0.25, DARK_WOOD)
    s.note("the tavern's sign on its bracket, the tankard painted on it")
    sx = -0.8
    s.span(sx, B - 0.5, hd + 0.2, sx + 0.06, B - 0.44, hd + 1.2, (0.12, 0.12, 0.12))
    s.span(
        sx + 0.01, B - 1.4, hd + 0.5, sx + 0.05, B - 0.6, hd + 1.15, (0.42, 0.24, 0.12)
    )
    s.span(
        sx - 0.025,
        B - 1.2,
        hd + 0.66,
        sx + 0.01,
        B - 0.8,
        hd + 0.99,
        (0.85, 0.70, 0.30),
    )
    s.span(
        sx + 0.05,
        B - 1.2,
        hd + 0.66,
        sx + 0.085,
        B - 0.8,
        hd + 0.99,
        (0.85, 0.70, 0.30),
    )
    s.note("the tavern's door and a lit window on the street")
    s.span(0.2, 0, hd + 0.2, 1.2, 1.9, hd + 0.24, (0.30, 0.20, 0.12))
    s.span(-2.0, 0.9, hd + 0.2, -1.0, 1.8, hd + 0.24, (0.95, 0.80, 0.45))
    s.note("bare narrow boards, plaster with a damp stain, a low beam")
    shell(
        s,
        W,
        D,
        H,
        B,
        (0.46, 0.36, 0.25),
        (0.78, 0.74, 0.64),
        (0.34, 0.25, 0.16),
        (0.70, 0.66, 0.58),
    )
    for i in range(1, 12):
        x = -hw + i * W / 12
        s.span(x - 0.01, B + 0.1, -hd, x + 0.01, B + 0.102, hd, (0.36, 0.27, 0.18))
    s.box(-1.2, B + 1.9, -hd + 0.01, 0.9, 0.7, 0.02, (0.64, 0.60, 0.50))
    s.note("one small window on the street")
    backWindow(s, 0.8, B + 1.5, 0.7, 0.7, -hd, (0.40, 0.30, 0.20))
    s.note("the narrow bunk: straw mattress, a thin grey blanket")
    bed(
        s,
        -hw + 0.5,
        B + 0.1,
        -0.7,
        0.8,
        1.9,
        (0.40, 0.29, 0.18),
        (0.70, 0.65, 0.50),
        (0.42, 0.42, 0.44),
        (0.80, 0.78, 0.70),
        height=0.35,
        head=0.55,
        foot=0.4,
    )
    s.note("a rickety table and a stool, a candle stub")
    table(s, 0.6, B + 0.1, 0.3, 0.9, 0.6, 0.72, (0.48, 0.38, 0.26), (0.40, 0.30, 0.20))
    s.cyl(0.6, B + 0.33, 0.85, 0.34, 0.45, (0.40, 0.30, 0.20))
    s.cyl(0.25, B + 0.86, 0.45, 0.06, 0.08, (0.92, 0.90, 0.80))
    s.note("the washstand: a jug in a basin on a crate")
    s.box(1.6, B + 0.4, -1.6, 0.5, 0.6, 0.4, (0.52, 0.40, 0.24))
    s.cyl(1.6, B + 0.75, -1.6, 0.36, 0.1, (0.86, 0.86, 0.82))
    s.cyl(1.65, B + 0.88, -1.6, 0.12, 0.22, (0.86, 0.86, 0.82))
    s.note("a coat on a peg")
    s.box(-hw + 0.06, B + 1.6, 1.2, 0.08, 0.08, 0.08, (0.30, 0.22, 0.14))
    s.box(-hw + 0.12, B + 1.15, 1.2, 0.12, 0.9, 0.45, (0.30, 0.36, 0.30))
    s.note("the one pole, cheap cane, being polished, a rag beside it")
    poleFlat(s, 0.6, B + 0.82, 0.25, 1.25, CANE, None)
    rag(s, 0.85, B + 0.82, 0.45)
    return s


def driftwoodShack():
    s = Scene(
        "FishE - home on the third rung: a driftwood shack of your own on the\n"
        "shingle, the harbour water along its east side. Rough grey boards, a\n"
        "pallet bed, a little stove, a crate table, a net on the wall, two\n"
        "poles - one with a reel. 13:00.\n"
        "Generated by art/gen_homes.py - edit that and re-run, not this.\n"
        "Provisional art (RFC 0025): see stills.json."
    )
    W, D, H = 5.0, 4.4, 2.3
    hw, hd = W / 2, D / 2
    camera(s, 0.78, shift=(1.1, 0, 0.3))
    s.note("the shingle, and the harbour water to the east")
    s.span(-80, -0.6, -80, hw + 1.6, 0.0, 80, (0.62, 0.58, 0.46))
    s.span(hw + 1.6, -0.9, -80, hw + 2.4, -0.12, 80, (0.42, 0.40, 0.33))
    s.span(hw + 1.6, -0.9, -80, 120, -0.2, 80, WATER)
    s.note("an upturned dinghy and a lobster pot on the stones")
    s.span(hw + 0.4, 0, -hd - 2.2, hw + 1.4, 0.35, -hd + 0.2, (0.22, 0.30, 0.38))
    s.span(hw + 0.6, 0.35, -hd - 2.1, hw + 1.2, 0.48, -hd + 0.1, (0.20, 0.27, 0.34))
    s.span(hw + 0.85, 0.48, -hd - 2.15, hw + 0.95, 0.52, -hd + 0.15, (0.40, 0.30, 0.20))
    s.box(hw + 0.6, 0.2, 0.9, 0.45, 0.4, 0.45, (0.42, 0.30, 0.18))
    s.box(hw + 0.6, 0.41, 0.9, 0.47, 0.03, 0.47, (0.30, 0.20, 0.12))
    s.note("driftwood boards, grey and bleached, with gaps the light comes through")
    s.span(-hw, 0.0, -hd, hw, 0.12, hd, (0.50, 0.46, 0.40))
    greys = [
        (0.56, 0.54, 0.50),
        (0.48, 0.46, 0.42),
        (0.62, 0.58, 0.52),
        (0.44, 0.40, 0.36),
        (0.52, 0.50, 0.47),
    ]
    n = 18
    for i in range(n):
        x0 = -hw - 0.15 + i * (W + 0.15) / n
        s.span(
            x0,
            0,
            -hd - 0.15,
            x0 + (W + 0.15) / n - 0.03,
            H - 0.1 * (i % 3 == 1),
            -hd,
            greys[i % 5],
        )
    n = 16
    for i in range(n):
        z0 = -hd + i * (D + 0.15) / n
        s.span(
            -hw - 0.15,
            0,
            z0,
            -hw,
            H - 0.08 * (i % 3 == 2),
            z0 + (D + 0.15) / n - 0.03,
            greys[(i + 2) % 5],
        )
    s.span(
        -hw - 0.2,
        H - 0.05,
        -hd - 0.2,
        hw + 0.15,
        H + 0.07,
        -hd - 0.05,
        (0.40, 0.36, 0.32),
    )
    s.span(
        -hw - 0.2, H - 0.05, -hd, -hw - 0.05, H + 0.07, hd + 0.15, (0.40, 0.36, 0.32)
    )
    s.span(hw - 0.15, 0, -hd, hw, 0.3, hd + 0.15, (0.48, 0.46, 0.42))
    s.span(-hw, 0, hd, hw, 0.3, hd + 0.15, (0.48, 0.46, 0.42))
    s.note("one window, a square of glass in a driftwood frame")
    backWindow(s, 0.9, 1.45, 0.8, 0.6, -hd, (0.36, 0.32, 0.28))
    s.note("a pallet bed on the floor under a patched blanket")
    s.box(-hw + 0.6, 0.2, -1.0, 1.0, 0.16, 2.0, (0.50, 0.40, 0.28))
    s.box(-hw + 0.6, 0.33, -1.0, 0.92, 0.12, 1.9, (0.74, 0.66, 0.46))
    s.box(-hw + 0.6, 0.41, -0.8, 0.95, 0.05, 1.3, (0.55, 0.28, 0.22))
    s.box(-hw + 0.4, 0.43, -0.6, 0.3, 0.06, 0.3, (0.32, 0.40, 0.55))
    s.box(-hw + 0.6, 0.45, -1.75, 0.5, 0.12, 0.3, (0.82, 0.80, 0.72))
    s.note("a crate table, a driftwood stool, a lantern on a hook")
    s.box(0.7, 0.4, 0.4, 1.4, 0.68, 0.8, (0.56, 0.44, 0.28))
    s.box(0.7, 0.4, 0.81, 1.3, 0.05, 0.02, (0.44, 0.34, 0.22))
    s.cyl(0.7, 0.25, 1.3, 0.4, 0.38, (0.52, 0.48, 0.42))
    s.box(0.2, 1.95, -hd + 0.15, 0.04, 0.3, 0.04, (0.2, 0.2, 0.2))
    s.cyl(0.2, 1.7, -hd + 0.15, 0.16, 0.24, (0.75, 0.55, 0.25))
    s.note("a little iron stove of your own, its pipe through the wall, a kettle on it")
    s.box(-0.5, 0.42, -hd + 0.4, 0.5, 0.6, 0.45, (0.14, 0.14, 0.15))
    s.cyl(-0.5, 1.45, -hd + 0.25, 0.12, 1.5, (0.16, 0.16, 0.17))
    s.cyl(-0.6, 0.78, -hd + 0.45, 0.2, 0.12, (0.45, 0.42, 0.38))
    s.note("a net hung on the west wall with its floats, a bucket, a tackle tin")
    for k in range(5):
        s.box(-hw + 0.04, 1.2 + 0.18 * k, 1.0, 0.03, 0.02, 1.6, (0.30, 0.34, 0.30))
    for k in range(6):
        s.box(-hw + 0.04, 1.55, 0.25 + 0.3 * k, 0.03, 0.8, 0.02, (0.30, 0.34, 0.30))
    for k in range(3):
        s.ball(-hw + 0.1, 2.0, 0.4 + 0.6 * k, 0.16, (0.25, 0.55, 0.45))
    s.cyl(1.9, 0.2, -1.4, 0.4, 0.4, (0.50, 0.52, 0.55))
    s.box(0.2, 0.8, 0.5, 0.3, 0.1, 0.2, (0.55, 0.20, 0.15))
    s.note("two poles: one with a reel on the crate being polished, one by the door")
    poleFlat(s, 0.75, 0.74, 0.3, 1.6, (0.52, 0.40, 0.25), STEEL)
    rag(s, 1.15, 0.74, 0.55)
    poleStanding(s, hw - 0.4, 0.12, -hd + 0.3, 2.0, CANE, None)
    return s


def cozyCottage():
    s = Scene(
        "FishE - home on the fourth rung: a whitewashed cottage with a garden.\n"
        "Flagged floor, a dresser of plates, a proper bed under a patchwork\n"
        "quilt, a hearth with a kettle, a rack of three poles. 13:00.\n"
        "Generated by art/gen_homes.py - edit that and re-run, not this.\n"
        "Provisional art (RFC 0025): see stills.json."
    )
    W, D, H = 7.0, 6.0, 2.8
    hw, hd = W / 2, D / 2
    camera(s, 1.0)
    s.note("the garden: grass, a path, a picket fence, a bed of flowers")
    s.box(0, -0.3, 0, 60, 0.6, 60, GRASS)
    for k in range(16):
        s.box(hw + 1.5, 0.4, -hd - 1 + k * 0.6, 0.06, 0.8, 0.08, (0.92, 0.92, 0.88))
    s.box(hw + 1.5, 0.6, -hd + 3.5, 0.04, 0.06, 9.5, (0.92, 0.92, 0.88))
    s.box(hw + 1.5, 0.25, -hd + 3.5, 0.04, 0.06, 9.5, (0.92, 0.92, 0.88))
    for k in range(7):
        s.ball(hw + 0.8, 0.2, -hd + 0.5 + k * 0.6, 0.35, (0.30, 0.52, 0.24))
        s.ball(
            hw + 0.8,
            0.38,
            -hd + 0.5 + k * 0.6,
            0.12,
            [(0.85, 0.30, 0.35), (0.95, 0.85, 0.30), (0.70, 0.45, 0.85)][k % 3],
        )
    s.note("stone flags, whitewashed walls, oak beams")
    shell(
        s,
        W,
        D,
        H,
        0.0,
        (0.56, 0.54, 0.50),
        (0.94, 0.92, 0.86),
        (0.40, 0.30, 0.20),
        (0.86, 0.84, 0.78),
    )
    for i in range(1, 7):
        s.span(
            -hw,
            0.1,
            -hd + i * D / 7 - 0.01,
            hw,
            0.102,
            -hd + i * D / 7 + 0.01,
            (0.44, 0.42, 0.40),
        )
    for i in range(1, 8):
        s.span(
            -hw + i * W / 8 - 0.01,
            0.1,
            -hd,
            -hw + i * W / 8 + 0.01,
            0.102,
            hd,
            (0.44, 0.42, 0.40),
        )
    s.note("two windows with a pot of geraniums on the sill")
    backWindow(s, -0.2, 1.7, 1.2, 1.0, -hd, (0.30, 0.42, 0.34))
    s.cyl(-0.5, 1.26, -hd + 0.15, 0.16, 0.16, (0.65, 0.35, 0.22))
    s.ball(-0.5, 1.42, -hd + 0.15, 0.2, (0.85, 0.25, 0.25))
    leftWindow(s, 1.6, 1.7, 1.2, 1.0, -hw, (0.30, 0.42, 0.34))
    s.note("the hearth in the corner, a kettle on the hob")
    s.span(1.6, 0, -hd, 3.2, 1.3, -hd + 0.5, (0.62, 0.60, 0.56))
    s.span(1.9, 0.1, -hd + 0.2, 2.9, 0.9, -hd + 0.52, (0.14, 0.12, 0.12))
    s.span(1.5, 1.3, -hd, 3.3, 1.4, -hd + 0.6, (0.40, 0.30, 0.20))
    s.span(1.8, 1.4, -hd, 3.0, H, -hd + 0.4, (0.66, 0.64, 0.60))
    s.cyl(2.4, 0.3, -hd + 0.35, 0.3, 0.25, (0.20, 0.20, 0.22))
    s.cyl(2.0, 1.46, -hd + 0.3, 0.12, 0.12, (0.75, 0.70, 0.50))
    s.cyl(2.8, 1.46, -hd + 0.3, 0.12, 0.12, (0.75, 0.70, 0.50))
    s.note("the bed under a patchwork quilt, a chest at its foot")
    quilt = [
        (0.70, 0.30, 0.28),
        (0.85, 0.75, 0.45),
        (0.35, 0.50, 0.65),
        (0.45, 0.60, 0.40),
    ]
    bed(
        s,
        -2.4,
        0.1,
        -1.6,
        1.3,
        2.0,
        (0.48, 0.32, 0.18),
        (0.94, 0.92, 0.86),
        quilt[0],
        (0.96, 0.96, 0.94),
    )
    for i in range(3):
        for j in range(4):
            s.box(
                -2.4 - 0.43 + i * 0.43,
                0.75,
                -1.6 - 0.35 + j * 0.35 + 0.2,
                0.42,
                0.012,
                0.34,
                quilt[(i + j) % 4],
            )
    s.box(-2.4, 0.35, -0.3, 1.0, 0.5, 0.5, (0.42, 0.28, 0.16))
    s.box(-2.4, 0.61, -0.3, 1.02, 0.04, 0.52, (0.36, 0.24, 0.14))
    s.note("the dresser against the west wall with its plates")
    s.span(-hw, 0.1, 0.8, -hw + 0.5, 1.0, 2.6, (0.46, 0.34, 0.20))
    s.span(-hw, 1.0, 0.8, -hw + 0.3, 2.1, 2.6, (0.46, 0.34, 0.20))
    s.span(-hw + 0.3, 1.0, 0.85, -hw + 0.32, 2.05, 2.55, (0.40, 0.28, 0.16))
    for shelf in (1.35, 1.75):
        s.span(-hw + 0.3, shelf - 0.02, 0.8, -hw + 0.4, shelf, 2.6, (0.40, 0.28, 0.16))
        for k in range(5):
            s.cyl(
                -hw + 0.34,
                shelf + 0.13,
                1.0 + k * 0.34,
                0.26,
                0.03,
                (0.92, 0.92, 0.96),
                dz=0.26,
            )
    s.note("a rag rug, a table with two chairs and a jug of flowers")
    rug(s, 0.4, 0.1, 0.4, 2.4, 1.8, (0.55, 0.35, 0.30), (0.35, 0.40, 0.55))
    table(s, 0.4, 0.1, 0.4, 1.4, 0.9, 0.76, WOOD, DARK_WOOD)
    chair(s, -0.6, 0.1, 0.4, DARK_WOOD, "-x")
    chair(s, 1.4, 0.1, 0.4, DARK_WOOD, "+x")
    s.cyl(0.0, 0.95, 0.65, 0.14, 0.2, (0.30, 0.45, 0.70))
    s.ball(0.0, 1.1, 0.65, 0.18, (0.95, 0.85, 0.30))
    s.note("a rack of three poles on the back wall, the best one on the table")
    s.span(-1.1, 2.15, -hd, -1.6 + 1.9, 2.25, -hd + 0.12, DARK_WOOD)
    s.span(-1.1, 0.3, -hd, -1.6 + 1.9, 0.4, -hd + 0.12, DARK_WOOD)
    for k, c in enumerate([CANE, (0.52, 0.40, 0.25), (0.30, 0.35, 0.30)]):
        poleStanding(
            s, -0.75 + k * 0.4 + 0.9, 0.12, -hd + 0.08, 2.3, c, STEEL if k else None
        )
    poleFlat(s, 0.45, 0.86, 0.3, 1.8, (0.45, 0.30, 0.18), STEEL)
    rag(s, 0.85, 0.86, 0.6)
    s.box(-0.1, 0.9, 0.15, 0.35, 0.12, 0.22, (0.30, 0.42, 0.30))
    return s


def sturdyCabin():
    s = Scene(
        "FishE - home on the fifth rung: a sturdy log cabin. Big and warm: a\n"
        "stone chimney with a fire in it, a double bed, a table for four, a\n"
        "bookshelf, a trophy fish over the door, a rack of five poles and a\n"
        "tackle chest. 13:00.\n"
        "Generated by art/gen_homes.py - edit that and re-run, not this.\n"
        "Provisional art (RFC 0025): see stills.json."
    )
    W, D, H = 9.0, 7.5, 3.2
    hw, hd = W / 2, D / 2
    camera(s, 1.27)
    s.note("the yard: grass, a woodpile, two pines")
    s.box(0, -0.3, 0, 80, 0.6, 80, GRASS)
    for k in range(4):
        for j in range(6):
            s.box(
                hw + 0.75,
                0.14 + k * 0.27,
                -hd + 0.6 + j * 0.27,
                0.5,
                0.26,
                0.26,
                (0.55, 0.40, 0.25) if (j + k) % 2 else (0.66, 0.50, 0.32),
            )
    s.span(hw + 0.4, 1.15, -hd + 0.35, hw + 1.15, 1.22, -hd + 2.3, DARK_WOOD)
    s.box(hw + 2.4, 0.25, -hd + 2.0, 0.5, 0.5, 0.5, (0.52, 0.38, 0.24))
    s.box(hw + 2.4, 0.62, -hd + 2.0, 0.06, 0.4, 0.06, (0.40, 0.30, 0.20))
    for tx, tz in ((-hw - 3.0, -hd - 3.5), (hw + 4.0, -hd - 2.0)):
        s.cyl(tx, 1.0, tz, 0.4, 2.0, (0.35, 0.24, 0.15))
        for k, d in enumerate((2.6, 2.0, 1.3)):
            s.ball(tx, 2.4 + k * 1.1, tz, d, (0.18, 0.34, 0.20))
    s.note("log walls, wide planks, a beam overhead")
    s.span(-hw, 0, -hd, hw, 0.12, hd, (0.58, 0.42, 0.26))
    for i in range(1, 12):
        x = -hw + i * W / 12
        s.span(x - 0.012, 0.12, -hd, x + 0.012, 0.122, hd, (0.42, 0.30, 0.18))
    logs = [(0.55, 0.38, 0.22), (0.47, 0.32, 0.18)]
    n = 11
    for i in range(n):
        y0 = i * H / n
        c = logs[i % 2]
        s.span(
            -hw - 0.25, y0, -hd - 0.28 + 0.03 * (i % 2), hw + 0.3, y0 + H / n, -hd, c
        )
        s.span(
            -hw - 0.28 + 0.03 * (i % 2), y0, -hd - 0.25, -hw, y0 + H / n, hd + 0.3, c
        )
        s.span(
            -hw - 0.4,
            y0 + 0.02,
            -hd - 0.4,
            -hw - 0.1,
            y0 + H / n - 0.02,
            -hd - 0.1,
            logs[1 - i % 2],
        )
    s.span(-hw - 0.3, H, -hd - 0.3, hw + 0.35, H + 0.25, -hd + 0.05, DARK_WOOD)
    s.span(-hw - 0.3, H, -hd, -hw + 0.05, H + 0.25, hd + 0.35, DARK_WOOD)
    s.span(hw, 0, -hd, hw + 0.3, 0.45, hd + 0.3, logs[0])
    s.span(-hw, 0, hd, hw, 0.45, hd + 0.3, logs[0])
    s.note("two windows on the back wall, one on the west")
    backWindow(s, -2.4, 1.9, 1.3, 1.1, -hd, DARK_WOOD)
    backWindow(s, 0.6, 1.9, 1.3, 1.1, -hd, DARK_WOOD)
    leftWindow(s, 0.8, 1.9, 1.3, 1.1, -hw, DARK_WOOD)
    s.note("the stone chimney breast and its fire")
    rocks = [(0.55, 0.53, 0.50), (0.48, 0.46, 0.44), (0.60, 0.57, 0.52)]
    for k in range(8):
        s.span(
            2.4,
            k * 0.4,
            -hd,
            4.0,
            (k + 1) * 0.4,
            -hd + 0.75 - 0.1 * (k > 3),
            rocks[k % 3],
        )
    s.span(2.7, 0.12, -hd + 0.3, 3.7, 1.1, -hd + 0.77, (0.10, 0.08, 0.08))
    s.span(2.3, 1.3, -hd, 4.1, 1.4, -hd + 0.85, DARK_WOOD)
    s.span(2.95, 0.15, -hd + 0.4, 3.45, 0.35, -hd + 0.65, (1.0, 0.52, 0.14))
    s.light(3.2, 0.6, -hd + 1.0, 7, (1.0, 0.55, 0.20), 2.0)
    s.cyl(2.6, 1.5, -hd + 0.4, 0.15, 0.2, BRASS)
    s.box(3.6, 1.6, -hd + 0.35, 0.3, 0.4, 0.08, (0.85, 0.80, 0.70))
    s.note("a double bed under a thick red quilt, a chest at its foot")
    bed(
        s,
        -3.2,
        0.12,
        -2.4,
        1.7,
        2.1,
        DARK_WOOD,
        (0.94, 0.92, 0.86),
        (0.62, 0.18, 0.15),
        (0.96, 0.96, 0.94),
        height=0.5,
        head=1.2,
        foot=0.7,
    )
    s.box(-3.2, 0.42, -0.95, 1.3, 0.6, 0.55, (0.48, 0.30, 0.16))
    s.box(-3.2, 0.42, -0.95, 1.32, 0.08, 0.57, BRASS)
    s.note("a bookshelf on the west wall")
    s.span(-hw, 0.12, 1.4, -hw + 0.08, 2.2, 2.8, DARK_WOOD)
    s.span(-hw, 0.12, 1.36, -hw + 0.42, 2.2, 1.42, DARK_WOOD)
    s.span(-hw, 0.12, 2.78, -hw + 0.42, 2.2, 2.84, DARK_WOOD)
    for k in range(5):
        s.span(-hw, 0.2 + k * 0.5, 1.4, -hw + 0.42, 0.25 + k * 0.5, 2.8, DARK_WOOD)
    books = [
        (0.55, 0.20, 0.18),
        (0.20, 0.32, 0.50),
        (0.30, 0.45, 0.28),
        (0.75, 0.62, 0.35),
    ]
    for shelf in range(4):
        y = 0.25 + shelf * 0.5
        for k in range(9):
            s.box(
                -hw + 0.25,
                y + 0.17,
                1.52 + k * 0.14,
                0.26,
                0.32 - 0.04 * (k % 3),
                0.11,
                books[(k + shelf) % 4],
            )
    s.note("a bear-skin rug, a table for four with a lantern")
    rug(s, 0.2, 0.12, 0.6, 3.0, 2.4, (0.48, 0.34, 0.22), (0.38, 0.26, 0.16))
    table(s, 0.2, 0.12, 0.6, 1.8, 1.1, 0.78, WOOD, DARK_WOOD, 0.09)
    chair(s, -0.95, 0.12, 0.6, DARK_WOOD, "-x")
    chair(s, 1.35, 0.12, 0.6, DARK_WOOD, "+x")
    chair(s, -0.2, 0.12, -0.25, DARK_WOOD, "-z")
    chair(s, 0.6, 0.12, -0.25, DARK_WOOD, "-z")
    s.cyl(-0.4, 1.0, 0.95, 0.16, 0.24, BRASS)
    s.cyl(-0.4, 1.0, 0.95, 0.1, 0.18, (1.0, 0.85, 0.50))
    s.note("the trophy fish on a board over the west window")
    s.box(-hw + 0.04, 2.85, 0.8, 0.04, 0.4, 1.1, DARK_WOOD)
    s.box(-hw + 0.1, 2.85, 0.8, 0.1, 0.22, 0.8, (0.45, 0.55, 0.50))
    s.box(-hw + 0.1, 2.85, 0.33, 0.06, 0.3, 0.12, (0.45, 0.55, 0.50))
    s.note("a rack of five poles, a tackle chest, waders on a peg")
    s.span(-1.2, 2.5, -hd, 0.0 + 0.0, 2.6, -hd + 0.14, DARK_WOOD)
    rods = [
        CANE,
        (0.52, 0.40, 0.25),
        (0.30, 0.35, 0.30),
        (0.25, 0.30, 0.45),
        (0.45, 0.20, 0.15),
    ]
    s.span(-1.55, 2.5, -hd, -0.75 + 1.95, 2.6, -hd + 0.14, DARK_WOOD)
    for k, c in enumerate(rods):
        poleStanding(
            s,
            -1.45 + k * 0.32,
            0.12,
            -hd + 0.08,
            2.6 - 0.05 * k,
            c,
            STEEL if k < 3 else BRASS,
        )
    s.box(1.8, 0.42, -hd + 0.5, 1.0, 0.6, 0.6, (0.30, 0.38, 0.30))
    s.box(1.8, 0.73, -hd + 0.5, 1.02, 0.05, 0.62, BRASS)
    s.box(-hw + 0.15, 1.2, 3.2, 0.12, 1.0, 0.3, (0.25, 0.32, 0.24))
    s.box(-hw + 0.06, 1.75, 3.2, 0.1, 0.08, 0.08, DARK_WOOD)
    s.note("the best pole on the table being polished, its reel off beside it")
    poleFlat(s, 0.3, 0.9, 0.5, 2.0, (0.30, 0.20, 0.12), BRASS)
    s.cyl(0.95, 0.94, 0.85, 0.12, 0.08, BRASS)
    rag(s, 0.7, 0.9, 0.85)
    return s


def waterfrontManor():
    s = Scene(
        "FishE - the top rung: the waterfront manor, standing on the harbour\n"
        "wall with the water along its east side and its own jetty and boat.\n"
        "Panelled walls, parquet, tall windows, a four-poster bed, a marble\n"
        "fireplace, a dining table for six, and a glass cabinet of polished\n"
        "poles with brass reels. 13:00.\n"
        "Generated by art/gen_homes.py - edit that and re-run, not this.\n"
        "Provisional art (RFC 0025): see stills.json."
    )
    W, D, H = 12.0, 9.0, 3.8
    hw, hd = W / 2, D / 2
    camera(s, 1.5, shift=(2.0, 0, 0.9))
    s.note("lawn behind, the harbour wall and the water along the east and south")
    s.span(-200, -0.6, -200, hw + 1.5, 0.0, hd + 1.5, GRASS)
    s.span(-60, -0.6, hd + 1.5, 60, 0.0, hd + 2.5, STONE)
    s.span(hw + 1.5, -0.6, -60, hw + 2.5, 0.0, hd + 2.5, STONE)
    s.span(-hw - 1.5, -0.3, -hd - 1.5, hw + 1.5, 0.01, hd + 1.5, (0.68, 0.64, 0.56))
    s.box(0, -1.2, 0, 400, 0.6, 400, WATER)
    s.note("the private jetty and the manor's boat")
    s.span(hw + 2.5, -0.15, -1.0, hw + 9.0, 0.0, 0.6, (0.48, 0.36, 0.22))
    for k in range(4):
        s.cyl(hw + 3.5 + k * 1.8, -0.6, -1.05, 0.2, 1.2, (0.30, 0.22, 0.14))
        s.cyl(hw + 3.5 + k * 1.8, -0.6, 0.65, 0.2, 1.2, (0.30, 0.22, 0.14))
    s.span(hw + 3.5, -0.85, 1.0, hw + 8.0, -0.25, 2.3, (0.92, 0.92, 0.90))
    s.span(hw + 3.6, -0.3, 1.1, hw + 7.9, -0.2, 2.2, (0.55, 0.38, 0.22))
    s.box(hw + 5.5, 1.2, 1.65, 0.1, 3.0, 0.1, (0.85, 0.82, 0.74))
    s.note("parquet floor, oak panelling below, sea-green walls above")
    shell(
        s,
        W,
        D,
        H,
        0.0,
        (0.55, 0.38, 0.22),
        (0.62, 0.74, 0.70),
        (0.92, 0.90, 0.84),
        (0.90, 0.88, 0.82),
    )
    for i in range(int(W / 0.5)):
        for j in range(int(D / 1.0)):
            if (i + j) % 2:
                s.span(
                    -hw + i * 0.5 + 0.01,
                    0.1,
                    -hd + j * 1.0 + 0.01,
                    -hw + i * 0.5 + 0.49,
                    0.103,
                    -hd + j * 1.0 + 0.99,
                    (0.62, 0.44, 0.26),
                )
    s.span(-hw, 0.1, -hd, hw, 1.2, -hd + 0.06, (0.42, 0.27, 0.15))
    s.span(-hw, 0.1, -hd, -hw + 0.06, 1.2, hd, (0.42, 0.27, 0.15))
    s.span(-hw, 1.2, -hd, hw, 1.26, -hd + 0.1, (0.92, 0.90, 0.84))
    s.span(-hw, 1.2, -hd, -hw + 0.1, 1.26, hd, (0.92, 0.90, 0.84))
    s.note("tall windows on the back and west walls")
    for x in (-3.8, 1.4):
        backWindow(s, x, 2.3, 1.3, 2.0, -hd, (0.92, 0.90, 0.84))
    for z in (0.2, 3.0):
        leftWindow(s, z, 2.3, 1.3, 2.0, -hw, (0.92, 0.90, 0.84))
    s.note("the marble fireplace, a clock on the mantel, a portrait of a boat")
    s.span(-1.6, 0.1, -hd, -0.2, 1.5, -hd + 0.4, (0.90, 0.88, 0.84))
    s.span(-1.3, 0.1, -hd + 0.2, -0.5, 1.0, -hd + 0.42, (0.10, 0.08, 0.08))
    s.span(-1.75, 1.5, -hd, -0.05, 1.6, -hd + 0.5, (0.94, 0.92, 0.88))
    s.span(-1.1, 0.12, -hd + 0.25, -0.7, 0.3, -hd + 0.4, (1.0, 0.55, 0.15))
    s.light(-0.9, 0.5, -hd + 0.9, 6, (1.0, 0.55, 0.20), 1.5)
    s.box(-0.9, 1.75, -hd + 0.3, 0.3, 0.3, 0.12, BRASS)
    s.cyl(-0.9, 1.78, -hd + 0.37, 0.18, 0.02, (0.95, 0.95, 0.90), dz=0.02)
    s.box(-0.9, 2.6, -hd + 0.04, 1.3, 0.9, 0.06, BRASS)
    s.box(-0.9, 2.6, -hd + 0.08, 1.15, 0.75, 0.04, (0.40, 0.58, 0.70))
    s.box(-0.9, 2.45, -hd + 0.1, 0.6, 0.15, 0.03, (0.55, 0.25, 0.18))
    s.box(-0.9, 2.72, -hd + 0.1, 0.04, 0.4, 0.03, (0.95, 0.95, 0.92))
    s.note("the four-poster bed, its canopy, a chest at its foot")
    bed(
        s,
        -4.4,
        0.1,
        -2.8,
        2.0,
        2.3,
        (0.38, 0.22, 0.12),
        (0.96, 0.96, 0.94),
        (0.30, 0.38, 0.62),
        (0.98, 0.98, 0.96),
        height=0.6,
        head=1.4,
        foot=0.8,
        posts=(2.6, (0.55, 0.15, 0.18)),
    )
    s.box(-4.4, 0.45, -1.2, 1.6, 0.6, 0.6, (0.38, 0.22, 0.12))
    s.box(-4.4, 0.45, -1.2, 1.62, 0.08, 0.62, BRASS)
    s.note("a fine rug, a dining table for six, candlesticks, a silver dish of fish")
    rug(s, 0.6, 0.1, 1.4, 5.0, 3.2, (0.62, 0.16, 0.16), (0.82, 0.68, 0.30))
    table(s, 0.6, 0.1, 1.4, 3.0, 1.2, 0.8, (0.40, 0.22, 0.12), (0.34, 0.18, 0.10), 0.1)
    for x in (-0.4, 0.6, 1.6):
        chair(s, x, 0.1, 0.45, (0.40, 0.22, 0.12), "-z")
        chair(s, x, 0.1, 2.35, (0.40, 0.22, 0.12), "+z")
    for x in (-0.3, 1.5):
        s.cyl(x, 1.0, 1.4, 0.08, 0.3, BRASS)
        s.cyl(x, 1.2, 1.4, 0.04, 0.12, (0.98, 0.96, 0.88))
    s.cyl(0.6, 0.93, 1.75, 0.5, 0.04, (0.82, 0.84, 0.86))
    s.note("armchairs by the west windows")
    for z in (1.0, 2.4):
        s.span(-hw + 0.5, 0.1, z - 0.4, -hw + 1.3, 0.55, z + 0.4, (0.20, 0.36, 0.30))
        s.span(-hw + 0.5, 0.55, z - 0.4, -hw + 0.7, 1.2, z + 0.4, (0.20, 0.36, 0.30))
        s.span(-hw + 0.5, 0.55, z - 0.4, -hw + 1.3, 0.8, z - 0.3, (0.20, 0.36, 0.30))
        s.span(-hw + 0.5, 0.55, z + 0.3, -hw + 1.3, 0.8, z + 0.4, (0.20, 0.36, 0.30))
    s.note("the glass cabinet of polished poles, brass reels, against the back wall")
    s.span(2.6, 0.1, -hd, 5.4, 0.5, -hd + 0.7, (0.38, 0.22, 0.12))
    s.span(2.6, 3.0, -hd, 5.4, 3.15, -hd + 0.7, (0.38, 0.22, 0.12))
    rods = [
        (0.30, 0.20, 0.12),
        (0.25, 0.30, 0.45),
        (0.45, 0.20, 0.15),
        (0.20, 0.35, 0.28),
        (0.60, 0.48, 0.30),
        (0.15, 0.15, 0.18),
        (0.50, 0.28, 0.12),
    ]
    for k, c in enumerate(rods):
        poleStanding(s, 2.85 + k * 0.38, 0.5, -hd + 0.3, 2.45, c, BRASS)
    for x in (2.62, 5.38):
        s.span(x - 0.03, 0.5, -hd, x + 0.03, 3.0, -hd + 0.7, BRASS)
    s.note("the trophy marlin over the cabinet")
    s.box(4.0, 3.45, -hd + 0.04, 2.0, 0.5, 0.05, (0.38, 0.22, 0.12))
    s.box(4.0, 3.45, -hd + 0.1, 1.5, 0.3, 0.1, (0.28, 0.40, 0.58))
    s.box(3.1, 3.45, -hd + 0.1, 0.3, 0.06, 0.06, (0.28, 0.40, 0.58))
    s.box(4.85, 3.45, -hd + 0.1, 0.15, 0.45, 0.08, (0.28, 0.40, 0.58))
    s.note("the chandelier over the table")
    s.box(0.6, H - 0.35, 1.4, 0.03, 0.7, 0.03, BRASS)
    s.cyl(0.6, H - 0.75, 1.4, 0.9, 0.06, BRASS)
    for dx, dz in ((-0.4, 0), (0.4, 0), (0, -0.4), (0, 0.4)):
        s.cyl(0.6 + dx, H - 0.66, 1.4 + dz, 0.05, 0.14, (0.98, 0.96, 0.88))
    s.note("the prized pole on the side table by the hearth, being polished")
    table(s, 1.6, 0.1, -hd + 1.4, 2.2, 0.6, 0.8, (0.40, 0.22, 0.12), (0.34, 0.18, 0.10))
    poleFlat(
        s, 1.6, 0.9, -hd + 1.35, 2.1, (0.14, 0.10, 0.08), BRASS, grip=(0.62, 0.48, 0.30)
    )
    rag(s, 2.35, 0.9, -hd + 1.55, (0.95, 0.95, 0.92))
    s.cyl(1.0, 0.94, -hd + 1.55, 0.1, 0.08, (0.85, 0.70, 0.35))
    return s


HOMES = {
    "home-rented": rentedRoom,
    "home-shack": driftwoodShack,
    "home-cottage": cozyCottage,
    "home-cabin": sturdyCabin,
    "home-manor": waterfrontManor,
}


def path(key):
    return os.path.join(ART, key + ".scene")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    stale = []
    for key, build in HOMES.items():
        text = build().text()
        if "--check" in argv:
            try:
                with open(path(key), encoding="utf-8") as f:
                    if f.read() != text:
                        stale.append(key)
            except OSError:
                stale.append(key)
        else:
            with open(path(key), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("wrote art/%s.scene" % key)
    if stale:
        print("stale (re-run art/gen_homes.py): %s" % ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
