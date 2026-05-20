#!/bin/sh
set -eu

REQUIREMENTS_FILE="${SYSCALL_DIG_REQUIREMENTS_FILE:-/requirements.txt}"
TARGET_DIR="${SYSCALL_DIG_PYTHON_TARGET:-/var/sandbox/sandbox-python/usr/local/lib/python3.11/dist-packages}"
HASH_FILE="$TARGET_DIR/.requirements.sha256"

if [ ! -s "$REQUIREMENTS_FILE" ] || ! grep -Eq '^[[:space:]]*[^#[:space:]]' "$REQUIREMENTS_FILE"; then
  echo "No Python dependencies to install."
  exit 0
fi

mkdir -p "$TARGET_DIR"

CURRENT_HASH="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"
if [ -f "$HASH_FILE" ] && [ "$(cat "$HASH_FILE")" = "$CURRENT_HASH" ]; then
  echo "Python dependencies are already installed."
  exit 0
fi

pip3 install \
  --break-system-packages \
  --upgrade \
  --target "$TARGET_DIR" \
  -r "$REQUIREMENTS_FILE"

printf '%s' "$CURRENT_HASH" > "$HASH_FILE"
