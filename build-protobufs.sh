#!/usr/bin/env sh
# Generate Python protobuf code from .proto files

PROTO_DIR="src/protobufs"
OUTPUT_DIR="src/generated"

mkdir -p "$OUTPUT_DIR/meshtastic"

echo "Generating Python protobuf code..."
for proto_file in "$PROTO_DIR"/meshtastic/*.proto; do
    python -m grpc_tools.protoc \
        -I"$PROTO_DIR" \
        --python_out="$OUTPUT_DIR" \
        --pyi_out="$OUTPUT_DIR" \
        "$proto_file"
done

# Create __init__.py
touch "$OUTPUT_DIR/__init__.py"
touch "$OUTPUT_DIR/meshtastic/__init__.py"
echo "Generated protobuf code in $OUTPUT_DIR"
