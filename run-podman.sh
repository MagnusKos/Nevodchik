#!/usr/bin/env sh


PROJECT="nevodchik"
IMAGE_NAME="localhost/${PROJECT}:latest"
CONTAINER_NAME="${PROJECT}-app"
TEST_CONTAINER_NAME="${PROJECT}-test"

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
  
  echo "Removing old images..."
  podman rmi -f "$IMAGE_NAME" 2>/dev/null || true
  podman rmi -f "${IMAGE_NAME%:latest}:test" 2>/dev/null || true
}

case "${1:-run}" in
    run)
        cleanup_containers

        echo "Building image..."
        podman build --no-cache --target worker -t "$IMAGE_NAME" .

        LOG_LEVEL="CRITICAL"

        while [ $# -gt 1 ]; do
            case "$2" in
                -c)
                    if [[ -z "$3" ]] || [[ "$3" == -* ]]; then
                        echo "Error: -c requires a value" >&2
                        exit 1
                    fi
                    config_value="$3"
                    shift 2
                    ;;
                -v)
                    if [[ -z "$3" ]] || [[ "$3" == -* ]]; then
                        echo "Error: -v requires a value (1-3)" >&2
                        exit 1
                    fi
                    verbose_value="$3"
                    # Validate -v value is 1, 2, or 3
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
                1)
                    LOG_LEVEL="WARNING"
                    ;;
                2)
                    LOG_LEVEL="INFO"
                    ;;
                3)
                    LOG_LEVEL="DEBUG"
                    ;;
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
        podman build --target tester -t "${IMAGE_NAME%:latest}:test" .
        
        echo "Running tests..."
        podman run \
            --name "$TEST_CONTAINER_NAME" \
            "${IMAGE_NAME%:latest}:test"
        
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
        podman build --target tester -t "${IMAGE_NAME%-latest}:test" .
        
        echo "Running tests (interactive)..."
        podman run \
            -it \
            --name "$TEST_CONTAINER_NAME" \
            "${IMAGE_NAME%-latest}:test" \
            pytest -v -s
        ;;
    
    logs)
        echo "Logs for $CONTAINER_NAME..."
        podman logs -f "$CONTAINER_NAME"
        ;;
    
    clean)
        cleanup_containers
        podman image prune -f 2>/dev/null || true
        echo "Cleaned up containers and images"
        ;;
    
    *)
        echo "Usage: ./run-podman.sh [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  run [option]         Build and run application"
        echo "  test                 Build and run tests"
        echo "  test-interactive     Run tests with verbose output"
        echo "  logs                 View application logs"
        echo "  clean                Remove containers"
        echo ""
        echo "If no command provided, then RUN will be used."
        echo ""
        echo "Run options:"
        echo "  -v [level]   verbose, level is a num: 1 (WARN), 2 (INFO), 3 (DEBUG)"
        echo "  -c [path]    config, path to the config-file to be used"
        exit 1
        ;;
esac