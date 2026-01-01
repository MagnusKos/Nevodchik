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
        echo "   Stopping $CONTAINER_NAME..."
        podman stop "$CONTAINER_NAME" || true
    fi
    
    if container_running "$TEST_CONTAINER_NAME"; then
        echo "   Stopping $TEST_CONTAINER_NAME..."
        podman stop "$TEST_CONTAINER_NAME" || true
    fi
    
    if container_exists "$CONTAINER_NAME"; then
        echo "   Removing $CONTAINER_NAME..."
        podman rm "$CONTAINER_NAME" || true
    fi
    
    if container_exists "$TEST_CONTAINER_NAME"; then
        echo "   Removing $TEST_CONTAINER_NAME..."
        podman rm "$TEST_CONTAINER_NAME" || true
    fi
}

case "${1:-run}" in
    run)
        echo "Building image..."
        podman build --target worker -t "$IMAGE_NAME" .
        
        cleanup_containers
        
        echo "Starting application container..."
        podman run \
            --name "$CONTAINER_NAME" \
            -v "$(pwd):/nevodchik" \
            -v /nevodchik/.venv \
            -e MQTT_HOST="${MQTT_HOST:-localhost}" \
            -e MQTT_PORT="${MQTT_PORT:-1883}" \
            -e MQTT_USER="${MQTT_USER:-user}" \
            -e MQTT_PASS="${MQTT_PASS:-pass}" \
            "$IMAGE_NAME"
        ;;
    
    test)
        echo "Building test image..."
        podman build --target tester -t "${IMAGE_NAME%:latest}:test" .
        
        cleanup_containers
        
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
        echo "Building test image..."
        podman build --target tester -t "${IMAGE_NAME%-latest}:test" .
        
        cleanup_containers
        
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
        echo "    run                  Build and run application"
        echo "    test                 Build and run tests"
        echo "    test-interactive     Run tests with verbose output"
        echo "    logs                 View application logs"
        echo "    clean                Remove containers"
        exit 1
        ;;
esac