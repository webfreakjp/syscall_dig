#!/bin/sh
set -eu

install-python-deps

# Fail fast with the actual Python traceback before starting the 500-run scan.
SYSCALL_DIG_ENABLE_NETWORK=false \
  ALLOWED_SYSCALLS="$(seq -s, 0 499)" \
  python3 cmd/test/syscall_dig/test.py

extract_detected_syscalls() {
  detected_line="$(
    printf '%s\n' "$1" |
    sed -n '/^Following syscalls are required:/p' |
    tail -n 1
  )"

  if [ -z "$detected_line" ]; then
    echo "Failed to parse the detected syscall list." >&2
    exit 1
  fi

  printf '%s' "${detected_line#*:}"
}

scan_network_disabled="$(
  SYSCALL_DIG_ENABLE_NETWORK=false \
    go run cmd/test/syscall_dig/main.go
)"
printf '\nScan with enable_network=false\n%s\n' "$scan_network_disabled"
detected_network_disabled="$(
  extract_detected_syscalls "$scan_network_disabled"
)"

scan_network_enabled="$(
  SYSCALL_DIG_ENABLE_NETWORK=true \
    go run cmd/test/syscall_dig/main.go
)"
printf '\nScan with enable_network=true\n%s\n' "$scan_network_enabled"
detected_network_enabled="$(
  extract_detected_syscalls "$scan_network_enabled"
)"

dify_sandbox_commit="$(git rev-parse --short HEAD 2>/dev/null || true)"
if [ -n "$dify_sandbox_commit" ]; then
  printf '\nDify sandbox commit: %s\n' "$dify_sandbox_commit"
fi

go run ./cmd/syscall_report \
  -detected-network-disabled "$detected_network_disabled" \
  -detected-network-enabled "$detected_network_enabled"
