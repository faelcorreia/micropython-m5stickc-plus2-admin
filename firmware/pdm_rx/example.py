from machine import I2S, Pin
import array

# M5StickC Plus2 internal SPM1423:
#   PDM clock = GPIO 0, PDM data = GPIO 34
# Requires the custom PDM firmware in this directory.
#
# Validated on hardware with:
#   - mono, right slot (the SPM1423 is wired to the right slot on this board)
#   - 32 kHz sample rate and the ESP-IDF 16x PDM downsample mode
#   - the first DMA block discarded (it can contain stale data)
#   - the DC offset removed before computing peak/RMS
mic = I2S(
    0,
    sck=Pin(0),
    sd=Pin(34),
    mode=I2S.PDM_RX,
    bits=16,
    format=I2S.MONO,
    rate=32000,
    ibuf=4096,
)

samples = array.array("h", [0] * 800)  # 25 ms at 32 kHz
mic.readinto(samples)  # discard the stale first DMA block
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

rms = int((energy / len(samples)) ** 0.5)
print("mean:", int(mean), "peak:", peak, "rms:", rms)
mic.deinit()
