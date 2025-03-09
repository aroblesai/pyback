FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/usr/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y curl

WORKDIR /usr/app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . .

RUN uv pip install .

RUN chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh"]
