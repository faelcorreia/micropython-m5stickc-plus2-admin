"""
MIT license
Copyright (c) 2024 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import Pin  # type: ignore
import libs.std.logging as logging


class ButtonController:
    def __init__(self, button: Pin, name) -> None:
        self.logger: logging.Logger = logging.getLogger("BUTTONCONTROLLER")
        self.button = button
        self.name = name
        self.events = {"on_release": [], "on_down": [], "on_press": [], "on_up": []}
        self.last_state = 1

    def process(self):
        temp_state = self.button.value()
        # On release
        if (self.last_state == 0) and (temp_state == 1):
            self._trigger_event("on_release")
        # On up
        elif (self.last_state == 1) and (temp_state == 1):
            self._trigger_event("on_up")
        # On press
        elif (self.last_state == 1) and (temp_state == 0):
            self._trigger_event("on_press")
        # On down
        else:
            self._trigger_event("on_down")
        self.last_state = temp_state

    def _trigger_event(self, event_type):
        if event_type in ["on_release", "on_press", "on_down"]:
            self.logger.info(f"{self.name} {event_type}")
        for callback in self.events[event_type]:
            callback()

    def register_event(self, event_type: str, callback):
        if event_type in self.events:
            self.events[event_type].append(callback)
