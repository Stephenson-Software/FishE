FROM python:3.12-slim

# No third-party deps: the game (and its web front-end) is stdlib-only —
# pygame is only imported lazily by the pygame front-end, which this image
# never selects, so it's deliberately not installed here. Matches the
# gateway-dashboard/fleet-dashboard services' "no wheel supply chain to keep
# patched" approach.
WORKDIR /app
COPY src/ ./src/
COPY examples/ ./examples/

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
