# Claude OAuth Gateway

OpenAI-compatible API gateway (FastAPI) that serves Claude models through the
Claude Code CLI, authenticated with your Claude subscription (OAuth) instead of
an API key.

Endpoints:

- `GET  /health`
- `GET  /v1/models`
- `POST /v1/chat/completions`

`/v1/*` requires `Authorization: Bearer <GATEWAY_API_KEY>`.

## Setup

1. Create the env file and set a real key:

        cp .env.example .env
        # edit GATEWAY_API_KEY

2. Build and start:

        docker compose build
        docker compose up -d

3. Log in to Claude (once; credentials persist in `./claude-config`):

        docker exec -it claude-oauth-gateway claude auth login

4. Check:

        docker exec -it claude-oauth-gateway claude --version
        docker exec -it claude-oauth-gateway claude auth status

## Usage

Point an OpenAI-compatible client at:

    http://localhost:8765/v1                  (from host)
    http://host.docker.internal:8765/v1       (from another container)

with the API key set to `GATEWAY_API_KEY` from `.env`.

## Configuration

See `.env.example`: `GATEWAY_API_KEY`, `DEFAULT_MODEL`, `AVAILABLE_MODELS`,
`LOG_LEVEL`, etc.

Persistent directories (git-ignored): `data/`, `claude-config/`, `claude-workspace/`.

## Updating vendored sources (only when updating)

The `app/runtime/vendor/claude_directsdk` package is copied from
NousResearch/hermes-official-plugins. It is already committed; re-run this
only to pull a newer version.

    mkdir -p app/runtime/vendor/claude_directsdk

    git clone --depth 1 --filter=blob:none --sparse \
      https://github.com/NousResearch/hermes-official-plugins.git \
      /tmp/hermes-official-plugins

    cd /tmp/hermes-official-plugins
    git sparse-checkout set claude-subscription-directsdk
    cd -

    SRC=/tmp/hermes-official-plugins/claude-subscription-directsdk
    DST=app/runtime/vendor/claude_directsdk
    for f in directsdk.py admission.py model_catalog.py directsdk_setup.py inert_mcp.py LICENSE; do
      cp "$SRC/$f" "$DST/"
    done

    touch app/runtime/vendor/__init__.py
    touch app/runtime/vendor/claude_directsdk/__init__.py

Then rebuild: `docker compose build && docker compose up -d`.
