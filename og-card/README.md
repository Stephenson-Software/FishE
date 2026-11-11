# Link-preview card

`web/og.png` is the picture a shared link to FishE unfurls with (`og:image`, `twitter:image` in `web/index.html`). It is drawn from [`card.json`](card.json) by [community-site-kit's `tools/og-card`](https://github.com/kingdom-community/community-site-kit/tree/5e3329e2f50d9700ad60979270557fb0e3de98f8/tools/og-card): a small 3D scene rendered headless with [Strata](https://github.com/Preponderous-Software/strata) 0.6.0, with the title over it. The scene is built from the seed alone and contains no game data. [`card.provenance.json`](card.provenance.json) records what made the committed PNG.

The PNG is pre-rendered and committed; CI never re-renders it. arcade serves only `index.html` and `game.zip` for a tak game, so the page links the card from GitHub's raw host (`main` branch).

## Changing the card

Edit `card.json`. If the picture or its text changes, rewrite `alt` to match; `tests/web/test_og_image.py` checks that the page's `og:image:alt` and `twitter:image:alt` equal it. Then, on Linux x86-64:

```sh
git clone https://github.com/kingdom-community/community-site-kit /tmp/csk
git -C /tmp/csk checkout 5e3329e2f50d9700ad60979270557fb0e3de98f8
python3 -m venv /tmp/og-venv
/tmp/og-venv/bin/pip install -r /tmp/csk/tools/og-card/requirements.txt
sudo apt-get install libegl1 libgl1-mesa-dri fonts-dejavu-core
/tmp/og-venv/bin/python /tmp/csk/tools/og-card/og_card.py og-card/card.json
```

Commit the PNG and both JSON files. Scrapers cache a card by its URL for days, so a materially new picture is best given a new file name.
