# syntax=docker/dockerfile:1
#
# Container image for mcp-leyes, published to ghcr.io/beg-lag/mcp-leyes by
# .github/workflows/release.yml and listed in the MCP Registry as an "oci" package.
#
#   docker run -i --rm ghcr.io/beg-lag/mcp-leyes:1.0.0                  # stdio
#   docker run --rm -p 8000:8000 ghcr.io/beg-lag/mcp-leyes:1.0.0 \
#     --transport http --host 0.0.0.0 --port 8000                      # streamable HTTP
#
# The image carries a snapshot of leyes-mx (bare clone plus index, about 30 MB), so it
# answers from the first call even with --network none. With network it fetches new
# reforms at most once a day. Mount a volume on /home/mcp/.cache/mcp-leyes to keep
# updates between runs. Build with --build-arg LEYES_SNAPSHOT=0 to skip the snapshot.

ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src
# Dependencies first, from the lock file, so code changes reuse this layer.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:${PYTHON_VERSION}-slim
# Ownership proof for the MCP Registry: must equal "name" in server.json.
LABEL io.modelcontextprotocol.server.name="io.github.BEG-lag/mcp-leyes"
# git is the database: mcp-leyes reads every version of every law through it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 mcp
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    MCP_LEYES_CACHE=/home/mcp/.cache/mcp-leyes
USER mcp
WORKDIR /home/mcp
ARG LEYES_SNAPSHOT=1
RUN if [ "$LEYES_SNAPSHOT" = "1" ]; then mcp-leyes sync; fi
ENTRYPOINT ["mcp-leyes"]
