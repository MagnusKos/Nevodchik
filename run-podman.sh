#!/usr/bin/env sh

if [ -t 1 ]; then
    INTERACTIVE="-it"
else
    INTERACTIVE=""
fi

podman run \
    --rm \
    --volume .:/nevodchik \
    --volume /nevodchik/.venv \
    $INTERACTIVE \
    $(podman build -q .) \
    "$@"