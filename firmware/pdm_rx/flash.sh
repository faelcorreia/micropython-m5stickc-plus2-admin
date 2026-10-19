#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-/dev/ttyACM0}"
DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD="$DIR/build"

if [ ! -f "$BUILD/micropython.bin" ]; then
    echo "Missing $BUILD/micropython.bin" >&2
    echo "Build the firmware first (see README.md)." >&2
    exit 1
fi

if command -v esptool.py >/dev/null 2>&1; then
    ESPTOOL=(esptool.py)
else
    ESPTOOL=(python3 -m esptool)
fi

echo "Flashing experimental PDM firmware to $PORT (this erases the flash)..."
"${ESPTOOL[@]}" --chip esp32 --port "$PORT" -b 460800 erase_flash
"${ESPTOOL[@]}" --chip esp32 --port "$PORT" -b 460800 \
    --before default_reset --after hard_reset \
    write_flash --flash_mode dio --flash_size 8MB --flash_freq 40m \
    0x1000 "$BUILD/bootloader.bin" \
    0x8000 "$BUILD/partition-table.bin" \
    0x10000 "$BUILD/micropython.bin"

echo "Done. Open the REPL or reset the device."
