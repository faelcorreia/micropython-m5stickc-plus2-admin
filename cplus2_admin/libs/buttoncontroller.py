from machine import Pin


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
