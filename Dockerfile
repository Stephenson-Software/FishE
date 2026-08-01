FROM python:3.12-slim

WORKDIR /app

# jsonschema is a real runtime dependency, not a test-only one: src/fishE.py
# imports it at module scope, so the game cannot start without it. pygame is
# deliberately absent — it is imported lazily by the pygame front-end only,
# which this image never selects.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY examples/ ./examples/
# The JSON Schemas the save-file readers validate against. Their paths are
# relative to the process cwd (see playerJsonReaderWriter.PLAYER_SCHEMA_PATH =
# "schemas/player.json"), which is /app here — so they must be copied in, or
# every save load/write raises FileNotFoundError.
COPY schemas/ ./schemas/

# Create the data/ directory (see saveFileManager.py's default
# data_directory="data", resolved relative to the process cwd -> /app/data
# here) and hand it to a non-root user before switching to it, so a named
# volume mounted over /app/data on first run inherits writable ownership.
RUN useradd --system --no-create-home fishe \
    && mkdir -p /app/data \
    && chown -R fishe:fishe /app/data
USER fishe

# WebUserInterface itself defaults to 127.0.0.1:8000 (unreachable from
# outside its own network namespace); UserInterfaceFactory's WEB branch reads
# these to override the bind address/port. 0.0.0.0 is required for Traefik
# (a different container on the same bridge network) to reach this server.
ENV FISHE_WEB_HOST=0.0.0.0
ENV FISHE_WEB_PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python3", "examples/web_app.py"]
