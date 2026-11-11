"""The link-preview card (og:image): web/og.png and the <meta> tags naming it.

The card is a 1200x630 PNG rendered with Strata and committed; nothing here
renders it. The alt text is "alt" in og-card/card.json.
"""

import html
import json
import os
import re
import struct

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
CARD = os.path.join(REPOSITORY_ROOT, "web", "og.png")
IMAGE_URL = "https://raw.githubusercontent.com/Stephenson-Software/FishE/main/web/og.png"


def page():
    with open(os.path.join(REPOSITORY_ROOT, "web", "index.html"), encoding="utf-8") as f:
        return f.read()


def meta(attribute, name):
    found = re.findall(r'<meta %s="%s" content="([^"]*)">' % (attribute, re.escape(name)), page())
    assert len(found) == 1, "%s=%s should appear once, found %d" % (attribute, name, len(found))
    return html.unescape(found[0])


def card_alt():
    with open(os.path.join(REPOSITORY_ROOT, "og-card", "card.json"), encoding="utf-8") as f:
        return json.load(f)["alt"]


def test_the_card_is_a_1200_by_630_png():
    with open(CARD, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    assert head[12:16] == b"IHDR"
    assert struct.unpack(">II", head[16:24]) == (1200, 630)


def test_the_card_stays_small_enough_for_scrapers():
    # Facebook and X refuse cards over 5 MB; stay well under.
    assert os.path.getsize(CARD) < 512 * 1024


def test_the_page_names_the_card_with_its_size_and_alt_text():
    assert meta("property", "og:image") == IMAGE_URL
    assert meta("name", "twitter:image") == IMAGE_URL
    assert meta("property", "og:image:type") == "image/png"
    assert meta("property", "og:image:width") == "1200"
    assert meta("property", "og:image:height") == "630"
    assert meta("name", "twitter:card") == "summary_large_image"
    alt = card_alt()
    assert 20 <= len(alt) <= 420
    assert meta("property", "og:image:alt") == alt
    assert meta("name", "twitter:image:alt") == alt


def test_the_preview_text_matches_the_page():
    assert meta("property", "og:title") == meta("name", "twitter:title")
    assert meta("property", "og:description") == meta("name", "twitter:description")
    assert meta("property", "og:description") == meta("name", "description")
    assert "<title>%s</title>" % meta("property", "og:title") in page()
