# --- Build Stage ---

FROM ghcr.io/astral-sh/uv:0.9.20-python3.14-alpine AS builder

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Don't redownload Python, we already have it
ENV UV_PYTHON_DOWNLOADS=0

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Set work directory inside the container
WORKDIR /nevodchik

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /nevodchik

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked



# --- Work Stage ---

FROM python:3.14-alpine

# --- Environment vars to be set externally ---
ENV MQTT_HOST="localhost"
ENV MQTT_PORT=1883
ENV MQTT_USER="user"
ENV MQTT_PASS="pass"

ENV IRC_HOST="localhost"
ENV IRC_PORT=6667
ENV IRC_NICK="Nevodchik"

ENV TG_TOKEN=""
# --- ---

# Create a new user
ENV USER="nevodchik"
RUN addgroup -S ${USER} \
    && adduser -D -G ${USER} -S ${USER}

# Copy the application from the builder
COPY --from=builder --chown=nevodchik:nevodchik /nevodchik /nevodchik

# Place executables in the environment at the front of the path
ENV PATH="/nevodchik/.venv/bin:$PATH"

# User to start an app
USER ${USER}

WORKDIR /nevodchik

# Run!
CMD ["nevodchik"]