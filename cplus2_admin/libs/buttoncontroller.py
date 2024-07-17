# Copyright (c) 2024 Rafael Correia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# https://github.com/faelcorreia/micropython-m5stickc-plus2-admin

from machine import Pin # type: ignore


class ButtonController:
    last_state = 0

    def __init__(self, button: Pin, name) -> None:
        self.button = button
        self.name = name
        self.events = {"on_release": [], "on_down": [], "on_press": [], "on_up": []}

    def process(self):
        temp_state = self.button.value()
        # On release
        if (self.last_state == 0) and (temp_state == 1):
            self.trigger_event("on_release")
        # On up
        elif (self.last_state == 1) and (temp_state == 1):
            self.trigger_event("on_up")
        # On press
        elif (self.last_state == 1) and (temp_state == 0):
            self.trigger_event("on_press")
        # On down
        else:
            self.trigger_event("on_down")
        self.last_state = temp_state

    def trigger_event(self, event_type):
        if event_type in ["on_release", "on_press", "on_down"]:
            print(f"{self.name} {event_type}")
        for callback in self.events[event_type]:
            callback()

    def register_event(self, event_type: str, callback):
        if event_type in self.events:
            self.events[event_type].append(callback)
