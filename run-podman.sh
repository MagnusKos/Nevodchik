#!/usr/bin/env bash
set -euo pipefail

PROJECT="nevodchik"
IMAGE_NAME="localhost/${PROJECT}:latest"
TEST_IMAGE_NAME="${IMAGE_NAME%:latest}:test"

CONTAINER_NAME="${PROJECT}-app"
TEST_CONTAINER_NAME="${PROJECT}-test"

PROJECT_LABEL="ru.magnuskos.nevodchik.project=${PROJECT}"

container_exists() {
  podman ps -a --format "{{.Names}}" | grep -q "^${1}$"
}

container_running() {
  podman ps --format "{{.Names}}" | grep -q "^${1}$"
}

cleanup_containers() {
  if container_running "$CONTAINER_NAME"; then
    echo "Stopping $CONTAINER_NAME..."
    podman stop "$CONTAINER_NAME" || true
  fi

  if container_running "$TEST_CONTAINER_NAME"; then
    echo "Stopping $TEST_CONTAINER_NAME..."
    podman stop "$TEST_CONTAINER_NAME" || true
  fi

  if container_exists "$CONTAINER_NAME"; then
    echo "Removing $CONTAINER_NAME..."
    podman rm -f "$CONTAINER_NAME" || true
  fi

  if container_exists "$TEST_CONTAINER_NAME"; then
    echo "Removing $TEST_CONTAINER_NAME..."
    podman rm -f "$TEST_CONTAINER_NAME" || true
  fi
}

usage() {
  cat <<'EOF'
Usage: ./run-podman.sh [COMMAND]

Commands:
  run [options]        Build and run application (target: worker)
  image                Build application image only (target: worker), do not run it
  test                 Build and run tests (target: tester)
  test-interactive     Run tests interactively (pytest -v -s)
  logs                 View application logs (only works if container exists)
  clean [--all]        Project-scoped cleanup (safe for other projects)
  help                 Show this help

If no command provided, then RUN will be used.

Run options (original behavior preserved):
  -v <level>   verbose level: 1 (WARNING), 2 (INFO), 3 (DEBUG)
  -c <path>    path to config file passed as CONFIG_FILE

Notes about cleanup:
  - This script labels images with: ru.magnuskos.nevodchik.project=nevodchik
  - clean (default) prunes only dangling images with that label
  - clean --all removes ALL images with that label, then prunes leftovers

Examples:
  ./run-podman.sh run -v 2 -c ./config.yml
  ./run-podman.sh test
  ./run-podman.sh test-interactive
  ./run-podman.sh clean
  ./run-podman.sh clean --all
EOF
}

CMD="${1:-run}"

case "$CMD" in
  image)
    cleanup_containers

    echo "Building image only (no run)..."
    podman build --target worker -t "$IMAGE_NAME" --label "$PROJECT_LABEL" .

    echo "Built: $IMAGE_NAME"
    echo "You can now run it via Podman / Podman Desktop with custom mounts, ports, envs, etc."
    ;;

  run)
    cleanup_containers

    echo "Building image..."
    # No forced --no-cache: allows reuse and reduces dangling artifacts
    podman build --target worker -t "$IMAGE_NAME" --label "$PROJECT_LABEL" .

    LOG_LEVEL="CRITICAL"
    config_value=""
    verbose_value=""

    while [ $# -gt 1 ]; do
      case "$2" in
        -c)
          if [[ -z "${3:-}" ]] || [[ "${3:-}" == -* ]]; then
            echo "Error: -c requires a value" >&2
            exit 1
          fi
          config_value="$3"
          shift 2
          ;;
        -v)
          if [[ -z "${3:-}" ]] || [[ "${3:-}" == -* ]]; then
            echo "Error: -v requires a value (1-3)" >&2
            exit 1
          fi
          verbose_value="$3"
          if [[ ! "$verbose_value" =~ ^[1-3]$ ]]; then
            echo "Error: -v value must be 1, 2, or 3 (got: $verbose_value)" >&2
            exit 1
          fi
          shift 2
          ;;
        *)
          echo "Error: Unknown argument '$2'" >&2
          exit 1
          ;;
      esac
    done

    if [[ -n "$verbose_value" ]]; then
      case "$verbose_value" in
        1) LOG_LEVEL="WARNING" ;;
        2) LOG_LEVEL="INFO" ;;
        3) LOG_LEVEL="DEBUG" ;;
      esac
    fi

    echo "Starting application container..."
    echo "Envs from args:"
    echo "  CONFIG_FILE=${config_value:-UNSET}"
    echo "  LOG_LEVEL=${LOG_LEVEL:-UNSET}"

    podman run \
      --rm \
      --name "$CONTAINER_NAME" \
      -e CONFIG_FILE="$config_value" \
      -e LOG_LEVEL="$LOG_LEVEL" \
      "$IMAGE_NAME"
    ;;

  test)
    cleanup_containers

    echo "Building test image..."
    podman build --target tester -t "$TEST_IMAGE_NAME" --label "$PROJECT_LABEL" .

    echo "Running tests..."
    podman run \
      --name "$TEST_CONTAINER_NAME" \
      "$TEST_IMAGE_NAME"

    TEST_EXIT=$?
    echo ""
    if [ $TEST_EXIT -eq 0 ]; then
      echo "All tests passed!"
    else
      echo "Tests failed with exit code $TEST_EXIT"
    fi
    exit $TEST_EXIT
    ;;

  test-interactive)
    cleanup_containers

    echo "Building test image..."
    podman build --target tester -t "$TEST_IMAGE_NAME" --label "$PROJECT_LABEL" .

    echo "Running tests (interactive)..."
    podman run \
      -it \
      --name "$TEST_CONTAINER_NAME" \
      "$TEST_IMAGE_NAME" \
      pytest -v -s
    ;;

  logs)
    echo "Logs for $CONTAINER_NAME..."
    podman logs -f "$CONTAINER_NAME"
    ;;

  clean)
    cleanup_containers

    if [[ "${2:-}" == "--all" ]]; then
      echo "Removing ALL images for label: $PROJECT_LABEL"
      podman images -q --filter "label=$PROJECT_LABEL" | xargs -r podman rmi -f
    fi

    echo "Pruning dangling images for label only: $PROJECT_LABEL"
    podman image prune -f --filter "label=$PROJECT_LABEL" 2>/dev/null || true
    echo "Cleaned up containers and project images"
    ;;

  help|-h|--help)
    usage
    ;;

  *)
    usage
    exit 1
    ;;
esac
