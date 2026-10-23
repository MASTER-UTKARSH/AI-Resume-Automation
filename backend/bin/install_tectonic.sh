#!/usr/bin/env bash
# Standalone Tectonic Engine Installer for Clyde
set -e

TECTONIC_VERSION="0.17.0"
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Installing Tectonic ${TECTONIC_VERSION} (${OS} ${ARCH})..."

if [ "$OS" = "Linux" ] && [ "$ARCH" = "x86_64" ]; then
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-x86_64-unknown-linux-musl.tar.gz"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-aarch64-apple-darwin.tar.gz"
elif [ "$OS" = "Darwin" ]; then
    URL="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-x86_64-apple-darwin.tar.gz"
else
    echo "Unsupported OS/Arch combination. Please install Tectonic manually: https://tectonic-typesetting.github.io/"
    exit 1
fi

echo "Fetching ${URL}..."
curl -fsSL "$URL" | tar -xz -C "$BIN_DIR"
chmod +x "$BIN_DIR/tectonic"
echo "Tectonic successfully installed at ${BIN_DIR}/tectonic"
"$BIN_DIR/tectonic" --version
