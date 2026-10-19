"""
MIT license
Copyright (c) 2024 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import Pin  # type: ignore
import libs.std.logging as logging
import libs.std.time as time


class ButtonController:
    """Edge-triggered button handling with simple debouncing.

    ``on_press``/``on_release`` fire on the transition, while ``on_down`` and
    ``on_up`` fire once for the resulting level. The events are intentionally
    edge-triggered: firing them from the main loop on every iteration would
    flood the log and the registered callbacks while a button is held.
    """

    DEBOUNCE_MS = 20

    def __init__(self, button: Pin, name) -> None:
        self.logger: logging.Logger = logging.getLogger("BUTTONCONTROLLER")
        self.button = button
        self.name = name
        self.events = {"on_release": [], "on_down": [], "on_press": [], "on_up": []}
        self.state = self.button.value()
        self.last_change_ms = time.ticks_ms()

    @property
    def is_pressed(self) -> bool:
        return self.state == 0

    def process(self):
        value = self.button.value()
        if value == self.state:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_change_ms) < self.DEBOUNCE_MS:
            return

        self.state = value
        self.last_change_ms = now
        if value == 0:
            self._trigger_event("on_press")
            self._trigger_event("on_down")
        else:
            self._trigger_event("on_release")
            self._trigger_event("on_up")

    def _trigger_event(self, event_type):
        if event_type in ["on_release", "on_press"]:
            self.logger.info(f"{self.name} {event_type}")
        for callback in self.events[event_type]:
            callback()

    def register_event(self, event_type: str, callback):
        if event_type in self.events:
            self.events[event_type].append(callback)
