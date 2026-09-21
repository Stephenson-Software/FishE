FROM python:3.12-slim

WORKDIR /app

# This image does not run the game — the browser does. web/serve.py only hands
# out the page, the Worker, and the game bundle; Pyodide then runs the Python
# game in the player's own tab, with that tab's IndexedDB holding the saves.
#
# Two consequences worth spelling out:
#   - The only pip install is tak, the kit the game imports from: it is
#     installed so web/build_zip.py can copy it into the bundle (and it is
#     what the browser runs), not because the server needs it. jsonschema is
#     loaded browser-side by web/game-worker.js, and the server here is pure
#     stdlib. git is needed for that one install and removed afterwards.
#   - No save directory, and no volume to persist. Every visitor gets their own
#     game and their own save slots, which is exactly what the server-backed
#     front-end (examples/web_app.py) could not give them.
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && pip install --no-cache-dir "tak @ git+https://github.com/Stephenson-Software/tak@v0.2.0" \
    && apt-get purge -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY src/ ./src/
COPY web/ ./web/
# The JSON Schemas the save-file readers validate against. Their paths are
# relative to the process cwd, which the Worker sets to the unpacked bundle —
# so these have to be copied in for build_zip.py to put them in the bundle, not
# for anything in this image to read.
COPY schemas/ ./schemas/
COPY version.txt ./

# Bundle the game for the browser to download. Built here rather than checked
# in so the bundle can never be a stale copy of src/.
RUN python3 web/build_zip.py

RUN useradd --system --no-create-home fishe
USER fishe

# web/serve.py defaults to 127.0.0.1 (unreachable from outside its own network
# namespace), so 0.0.0.0 is required for Traefik — a different container on the
# same bridge network — to reach it.
ENV FISHE_WEB_HOST=0.0.0.0
ENV FISHE_WEB_PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python3", "web/serve.py"]
