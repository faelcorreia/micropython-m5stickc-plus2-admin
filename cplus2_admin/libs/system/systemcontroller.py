"""
MIT license
Copyright (c) 2024-2026 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

import gc
import machine  # type: ignore
import os
import libs.std.time as time


class SystemController:
    """Collects device health information for the admin page."""

    def __init__(self, battery=None) -> None:
        self.battery = battery
        self.started_ms = time.ticks_ms()

    def info(self) -> dict:
        mem_alloc = gc.mem_alloc()
        mem_free = gc.mem_free()

        statvfs = os.statvfs(".")
        flash_total = statvfs[1] * statvfs[2]
        flash_free = statvfs[1] * statvfs[3]

        uname = os.uname()
        result = {
            "system": uname[0],
            "release": uname[2],
            "version": uname[3],
            "machine": uname[4],
            "frequency": machine.freq(),
            "uptime_ms": time.ticks_diff(time.ticks_ms(), self.started_ms),
            "ram": {
                "used": mem_alloc,
                "free": mem_free,
                "total": mem_alloc + mem_free,
            },
            "flash": {
                "used": flash_total - flash_free,
                "free": flash_free,
                "total": flash_total,
            },
        }

        if self.battery is not None:
            result["battery"] = self.battery.read()

        return result
