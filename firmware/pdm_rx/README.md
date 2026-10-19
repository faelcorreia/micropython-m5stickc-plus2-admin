# SPM1423 PDM microphone support

The M5StickC Plus2 has an SPM1423 PDM microphone connected to **GPIO 0**
(clock) and **GPIO 34** (data).

Stock MicroPython **does not expose PDM RX** on the ESP32. As of October 2026:

- the upstream `machine.I2S` API still has no `PDM_RX` mode;
- PR [micropython#14176](https://github.com/micropython/micropython/pull/14176)
  ("ports/esp32: Add PDM RX feature to I2S") is still **open** (opened in March
  2024, last updated in April 2026);
- a new `machine.PDM` API is being developed, but initially for the Zephyr port
  (PR [micropython#18287](https://github.com/micropython/micropython/pull/18287)).

This directory contains an adapted version of PR #14176 for **MicroPython
v1.29.0**. It adds `I2S.PDM_RX` to the ESP32 port and uses the ESP-IDF
PDM-to-PCM hardware filter.

## What the patch changes

- `extmod/machine_i2s.c`: makes `ws` optional and accepts `PDM_RX` for reads.
- `ports/esp32/machine_i2s.c`:
  - initializes the ESP-IDF `i2s_channel_init_pdm_rx_mode()`;
  - uses 16-bit PCM output from the PDM filter and the `I2S_PDM_DSR_16S`
    downsample mode;
  - uses the **right** PDM slot for mono, which is how the SPM1423 is wired on
    the M5StickC Plus2 (the same default used by M5Unified);
  - reads PDM data directly (the upstream I2S read path is designed for
    32-bit stereo DMA frames and would otherwise skip samples);
  - keeps the standard I2S RX/TX behavior untouched.
- `ports/esp32/mpconfigport.h`: enables the new mode when the SoC supports
  PDM RX.
- `docs/library/machine.I2S.rst`: documents the new mode.

The patch was validated on a physical M5StickC Plus2: mono capture at 32 kHz
works, responds to sound, and returns centered PCM after the DC offset is
removed. The first DMA block after opening the port can be stale, so the
example and the admin controller discard it.

## Build

Apply the patch to a clean MicroPython v1.29.0 checkout:

```bash
cd micropython
git checkout v1.29.0
git apply /path/to/firmware/pdm_rx/micropython-v1.29.0-pdm-rx.patch
```

Then follow the normal build instructions in the project README, including
the 8 MiB flash-size change. The PDM patch was compiled here with ESP-IDF
v5.5.1 for `ESP32_GENERIC` with `BOARD_VARIANT=SPIRAM`.

## Flash

The `build/` directory contains binaries produced by that build:

- `bootloader.bin`
- `partition-table.bin`
- `micropython.bin`

They are experimental and target the M5StickC Plus2 (ESP32, 8 MiB flash,
SPIRAM). You can flash them with:

```bash
./flash.sh /dev/ttyACM0
```

This erases the flash, so copy any files you want to keep first. Alternatively,
build and use `make ... deploy` as described in the main README.

## Usage

```python
from machine import I2S, Pin
import array

mic = I2S(
    0,
    sck=Pin(0),       # PDM clock (MIC_CLK)
    sd=Pin(34),       # PDM data  (MIC_DATA)
    mode=I2S.PDM_RX,
    bits=16,
    format=I2S.MONO,
    rate=32000,
    ibuf=4096,
)

samples = array.array("h", [0] * 800)  # 25 ms at 32 kHz
mic.readinto(samples)  # discard stale first DMA block
mic.readinto(samples)  # fresh data

total = 0
for sample in samples:
    total += sample
mean = total / len(samples)

peak = 0
energy = 0
for sample in samples:
    centered = sample - mean
    value = centered if centered >= 0 else -centered
    if value > peak:
        peak = value
    energy += centered * centered

print("mean:", int(mean), "peak:", peak, "rms:", int((energy / len(samples)) ** 0.5))
mic.deinit()
```

The admin page exposes this through `GET /api/microphone/level` and the
**Microphone (experimental)** button. On stock firmware the endpoint returns
HTTP 503 with an explanatory message instead of breaking the page.

## Troubleshooting

- **All samples are zero**: the microphone may be wired to the other PDM slot.
  The M5StickC Plus2 uses the right slot (the default in this patch). For a
  board wired to the left slot, change the mono `slot_mask` to
  `I2S_PDM_SLOT_LEFT` in `ports/esp32/machine_i2s.c`, or use
  `format=I2S.STEREO` and inspect both channels.
- **The first measurement looks like garbage / full-scale DC**: the first DMA
  block after opening the port can be stale. Discard the first `readinto()` as
  the example and the admin controller do.
- **Recording is very quiet**: the SPM1423 output level is low and the
  ESP32 PDM filter has a DC offset. Remove the mean before computing RMS, and
  apply gain in software if needed. The admin page reports the DC-corrected
  peak/RMS.
- **Sample rate**: 32 kHz with the 16x downsample mode produced clean data on
  the M5StickC Plus2. 16 kHz also works but showed a larger DC offset in our
  tests; it can be used after DC removal.
- **Microphone values are noisy**: this is expected for a raw MEMS microphone;
  apply a high-pass filter and smoothing in your application.

## Status and attribution

This is **experimental** and has not yet been tested on a physical
M5StickC Plus2 here. The adaptation is based on PR #14176 by Lana-chan
(MIT-licensed MicroPython code), with fixes for the v1.29.0 read path and the
ESP-IDF 5.5 API.
