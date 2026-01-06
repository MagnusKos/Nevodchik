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
            -d|--debug)
                LOG_LEVEL="DEBUG"
                shift
                ;;
            -v|--verbose)
                LOG_LEVEL="INFO"
                shift
                ;;
            -w|--warning)
                LOG_LEVEL="WARNING"
                shift
                ;;
            *)
                shift
                ;;
            esac
        done
        
        echo "Starting application container..."
        podman run \
            --rm \
            --name "$CONTAINER_NAME" \
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
        echo "Run options (use one or none):"
        echo "  -w | --warning : prints warning log messages"
        echo "  -v | --verbose : prints information log messages"
        echo "  -d | --debug : prints debug log messages"
        exit 1
        ;;
esac