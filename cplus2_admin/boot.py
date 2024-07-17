from machine import Pin

# Set up Hold PIN to keep device on after USB disconnect
hold = Pin(4, Pin.IN, Pin.PULL_UP)
hold.on()