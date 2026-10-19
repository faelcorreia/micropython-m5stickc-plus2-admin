"""
MIT license
Copyright (c) 2024-2026 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin

Optional SPM1423 microphone support.

Stock MicroPython does not expose PDM RX on the ESP32. This controller is
therefore only usable with a custom firmware that provides I2S.PDM_RX (see
firmware/pdm_rx/README.md). On stock firmware it reports itself as unavailable
instead of breaking the rest of the admin page.
"""

from machine import I2S, Pin  # type: ignore
import array


class MicrophoneController:
    """Records short 16-bit mono buffers from the internal PDM microphone."""

    PDM_CLOCK_PIN = 0
    PDM_DATA_PIN = 34
    # 32 kHz with the 16x PDM downsample mode gives a 2.048 MHz PDM clock,
    # which is inside the SPM1423 range and produced clean data on hardware.
    SAMPLE_RATE = 32000
    DEFAULT_SAMPLES = 800  # 25 ms at 32 kHz

    def __init__(self) -> None:
        self.available = hasattr(I2S, "PDM_RX")
        self._i2s = None
        self._error = None

    def _ensure_open(self):
        if not self.available:
            raise RuntimeError(
                "This firmware does not expose I2S.PDM_RX. "
                "Use the custom firmware from firmware/pdm_rx/."
            )
        if self._i2s is not None:
            return
        try:
            self._i2s = I2S(
                0,
                sck=Pin(self.PDM_CLOCK_PIN),
                sd=Pin(self.PDM_DATA_PIN),
                mode=I2S.PDM_RX,
                bits=16,
                format=I2S.MONO,
                rate=self.SAMPLE_RATE,
                ibuf=4096,
            )
        except Exception as error:
            self._error = str(error)
            raise RuntimeError(f"Could not start the PDM microphone: {error}")

    def level(self, samples=DEFAULT_SAMPLES) -> dict:
        """Read a short buffer and return its DC-corrected peak and RMS values."""
        samples = max(64, min(4096, int(samples)))
        self._ensure_open()

        buffer = array.array("h", [0] * samples)
        # The first read after opening (and the first read after a long idle
        # period) can contain stale DMA data. Discard it and analyze the next
        # block, which is fresh.
        self._i2s.readinto(buffer)
        self._i2s.readinto(buffer)

        total = 0
        for sample in buffer:
            total += sample
        mean = total / samples

        peak = 0
        energy = 0
        for sample in buffer:
            centered = sample - mean
            value = centered if centered >= 0 else -centered
            if value > peak:
                peak = value
            energy += centered * centered

        rms = int((energy / samples) ** 0.5)
        return {
            "samples": samples,
            "sample_rate": self.SAMPLE_RATE,
            "peak": peak,
            "rms": rms,
            "mean": int(mean),
        }

    def deinit(self):
        if self._i2s is not None:
            self._i2s.deinit()
            self._i2s = None
