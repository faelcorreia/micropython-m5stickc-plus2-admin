from machine import Pin  # type: ignore

# Drive the power-hold pin high to keep the device on after USB disconnect.
hold = Pin(4, Pin.OUT, value=1)