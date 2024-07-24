"""
MIT license
Copyright (c) 2024 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import Pin  # type: ignore


class LEDController:
    def __init__(self, pin: Pin) -> None:
        self.pin = pin
        self.pin.off()
        self.state = False

    def is_on(self):
        return self.state

    def on(self):
        self.pin.on()
        self.state = True

    def off(self):
        self.pin.off()
        self.state = False

    def toggle(self):
        if self.state:
            self.off()
        else:
            self.on()
