#!/bin/sh
set -eu

CONFIG_FILE="${1:-/src/internal/static/config_default_amd64.go}"
SANDBOX_ROOT="${2:-/var/sandbox/sandbox-python}"

copy_path() {
  src="$1"
  dest="$SANDBOX_ROOT$src"

  if [ ! -e "$src" ]; then
    return 0
  fi

  mkdir -p "$(dirname "$dest")"
  cp -a "$src" "$dest"
}

if [ -f "$CONFIG_FILE" ]; then
  sed -n 's/.*"\(\/[^"]*\)".*/\1/p' "$CONFIG_FILE" | while IFS= read -r requirement; do
    copy_path "$requirement"
  done
fi

# The current base image uses Python 3.11 even if upstream defaults may point
# at another Python minor version. Keep these paths available for this image's
# interpreter and for runtime pip installs.
copy_path /usr/lib/python3.11
copy_path /usr/local/lib/python3.11

mkdir -p "$SANDBOX_ROOT/tmp"
chmod 1777 "$SANDBOX_ROOT/tmp"
