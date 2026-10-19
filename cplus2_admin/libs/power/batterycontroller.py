"""
MIT license
Copyright (c) 2024-2026 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import ADC, Pin  # type: ignore


class BatteryController:
    """Reads the M5StickC Plus2 battery voltage from GPIO 38.

    The battery is connected to the ADC through a 1:2 voltage divider, so the
    measured voltage must be multiplied by two. GPIO 38 is on the ESP32 ADC1
    and needs 11 dB attenuation to cover the battery range.
    """

    ADC_PIN = 38
    VOLTAGE_DIVIDER = 2
    MIN_MV = 3300
    MAX_MV = 4150
    DEFAULT_SAMPLES = 8

    def __init__(self, pin=ADC_PIN, samples=DEFAULT_SAMPLES) -> None:
        self.adc = ADC(Pin(pin, Pin.IN))
        self.samples = samples
        try:
            # 11 dB attenuation gives an input range of roughly 0-3.1 V.
            self.adc.atten(ADC.ATTN_11DB)
        except (AttributeError, ValueError):
            # Older ports may expose a different attenuation API.
            pass
        self._mv = None

    def read_mv(self) -> int:
        """Return the battery voltage in millivolts."""
        total_uv = 0
        for _ in range(self.samples):
            total_uv += self.adc.read_uv()
        mv = round(total_uv / self.samples / 1000 * self.VOLTAGE_DIVIDER)
        self._mv = mv
        return mv

    def read_percentage(self) -> int:
        """Return the battery level as a 0-100 percentage.

        The curve mirrors M5Stack's own implementation: 3.30 V is treated as
        empty and 4.15 V as full. LiPo voltage is not linear, so this is only
        an approximation, but it is good enough for a status display.
        """
        mv = self.read_mv()
        level = round((mv - self.MIN_MV) * 100 / (self.MAX_MV - self.MIN_MV))
        return max(0, min(100, level))

    def read(self) -> dict:
        mv = self.read_mv()
        level = round((mv - self.MIN_MV) * 100 / (self.MAX_MV - self.MIN_MV))
        return {
            "voltage": mv / 1000,
            "millivolts": mv,
            "percentage": max(0, min(100, level)),
        }
