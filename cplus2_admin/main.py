from machine import I2C, Pin, SPI, ADC  # type: ignore
from libs.st7789 import ST7789, ColorMode_16bit
from libs.pcf8563 import PCF8563
from libs.mpu6886 import MPU6886, SF_G, SF_DEG_S
from libs.wlancontroller import WLANController
from libs.webcontroller import WebController
from libs.buttoncontroller import ButtonController
from libs.ledcontroller import LEDController


class Admin:
    last_button_state = 0

    adc = ADC(Pin(38, Pin.IN))
    battery_uv = adc.read_uv()

    # Set up M5StickC Plus2 I2C
    i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)

    # Set up M5StickC Plus2 LED
    led = Pin(19, Pin.OUT)

    # Set up M5StickC Plus2 Button A
    button_a = Pin(37, Pin.IN)

    # Set up M5StickC Plus2 Button B
    button_b = Pin(39, Pin.IN)

    # Set up M5StickC Plus2 Button C
    button_c = Pin(35, Pin.IN)

    # Set up M5StickC Plus2 LCD Backlight
    backlight = Pin(27, Pin.OUT)

    # Set up BM8563 RTC (clone of the NXP PCF8563)
    rtc = PCF8563(i2c)

    # Set up M5StickC Plus2 SPI
    spi = SPI(
        1,
        baudrate=20000000,
        phase=0,
        polarity=1,
        sck=Pin(13, Pin.OUT),
        miso=Pin(4, Pin.IN),
        mosi=Pin(15, Pin.OUT),
    )

    # Set up ST7789 LCD
    display = ST7789(
        spi=spi,
        width=240,
        height=135,
        xstart=40,
        ystart=52,
        reset=Pin(12, Pin.OUT),
        dc=Pin(14, Pin.OUT),
        cs=Pin(5, Pin.OUT),
        buf=bytearray(4096),
        color_mode=ColorMode_16bit,
    )
    display.change_orientation("RLANDSCAPE")

    # Set up MPU6886 Sensor
    sensor = MPU6886(i2c, accel_sf=SF_G, gyro_sf=SF_DEG_S)

    def __init__(self) -> None:
        self.create_led_controller()
        self.create_network()
        self.create_button_controllers()

    def create_led_controller(self):
        self.ledcontroller = LEDController(self.led)

    def create_button_controllers(self):
        self.button_a_controller = ButtonController(self.button_a, "Button A")
        self.button_a_controller.register_event("on_press", self.ledcontroller.on)
        self.button_a_controller.register_event("on_release", self.ledcontroller.off)

        self.button_b_controller = ButtonController(self.button_b, "Button B")
        self.button_b_controller.register_event("on_press", self.ledcontroller.on)
        self.button_b_controller.register_event("on_release", self.ledcontroller.off)

        self.button_c_controller = ButtonController(self.button_c, "Button C")
        self.button_c_controller.register_event("on_press", self.ledcontroller.on)
        self.button_c_controller.register_event("on_release", self.ledcontroller.off)

    def create_network(self):
        self.wlancontroller = WLANController()
        self.wlancontroller.configure_ap()

        self.webcontroller = WebController(
            self.wlancontroller,
            self.ledcontroller,
            self.backlight,
            self.display,
            self.sensor,
            self.rtc,
        )
        self.webcontroller.start()


if __name__ == "__main__":
    admin = Admin()
    print("Program started.")
    print("Initializing infinite loop...\n")
    while True:
        # Process events from Button A
        admin.button_a_controller.process()

        # Process events from Button B
        admin.button_b_controller.process()

        # Process events from Button C
        admin.button_c_controller.process()

        # Process Web server requests
        admin.webcontroller.process()
