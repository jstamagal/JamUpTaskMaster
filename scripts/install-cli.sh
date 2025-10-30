#!/bin/bash
# Install jt CLI tool to PATH

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JT_PATH="$SCRIPT_DIR/jt"

# Determine install location
if [ -d "$HOME/.local/bin" ]; then
    INSTALL_DIR="$HOME/.local/bin"
elif [ -d "$HOME/bin" ]; then
    INSTALL_DIR="$HOME/bin"
else
    mkdir -p "$HOME/.local/bin"
    INSTALL_DIR="$HOME/.local/bin"
fi

echo "Installing jt to $INSTALL_DIR"

# Create symlink
ln -sf "$JT_PATH" "$INSTALL_DIR/jt"

echo "✓ Installed: jt"
echo ""
echo "Test it: jt ls"
echo ""

# Check if in PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "⚠️  Add to your shell rc file:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
