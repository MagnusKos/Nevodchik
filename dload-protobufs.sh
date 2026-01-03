#!/usr/bin/env sh
# Download and extract meshtastic protobufs

PROTOBUFS_VERSION="v2.7.17"
PROTOBUFS_URL="https://github.com/meshtastic/protobufs/archive/refs/tags/${PROTOBUFS_VERSION}.zip"
PROTO_DIR="src/protobufs"

echo "Downloading meshtastic protobufs ${PROTOBUFS_VERSION}..."
curl -L "$PROTOBUFS_URL" -o /tmp/protobufs.zip
unzip -q /tmp/protobufs.zip -d /tmp/
mkdir -p "$PROTO_DIR"
cp -r /tmp/protobufs-*/meshtastic "$PROTO_DIR/"

echo "Protobufs downloaded to $PROTO_DIR"

rm -f /tmp/protobufs.zip
rm -rf /tmp/protobufs-*
