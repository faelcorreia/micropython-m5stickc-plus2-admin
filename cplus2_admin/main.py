from machine import I2C, Pin, SPI, ADC, PWM  # type: ignore
from libs.display.st7789 import ST7789, ColorMode_16bit
from libs.rtc.pcf8563 import PCF8563
from libs.sensor.mpu6886 import MPU6886, SF_G, SF_DEG_S
from libs.network.wlancontroller import WLANController
from libs.network.webcontroller import WebController
from libs.button.buttoncontroller import ButtonController
from libs.led.ledcontroller import LEDController
from libs.audio.buzzercontroller import BuzzerController
import libs.std.logging as logging
import gc
import os

logging.basicConfig(
    level=logging.INFO, format="%(name)s %(asctime)s %(levelname)s %(message)s"
)
logger: logging.Logger = logging.getLogger("MAIN")


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
        buf=bytearray(64800),  # Image size: 240x135x2
        color_mode=ColorMode_16bit,
    )
    display.change_orientation("RLANDSCAPE")

    # Set up MPU6886 Sensor
    sensor = MPU6886(i2c, accel_sf=SF_G, gyro_sf=SF_DEG_S)

    # Set up M5StickC Plus2 Buzzer
    buzzer = PWM(Pin(2, Pin.OUT), duty=0)
    buzzer.deinit()

    def __init__(self) -> None:
        # Create LED Controller
        self.ledcontroller = LEDController(self.led)

        # Create Buzzer Controller
        self.buzzercontroller = BuzzerController(self.buzzer)

        # Create network
        self.wlancontroller = WLANController()
        self.wlancontroller.configure_ap()

        self.webcontroller = WebController(
            self.wlancontroller,
            self.ledcontroller,
            self.backlight,
            self.display,
            self.sensor,
            self.rtc,
            self.buzzercontroller,
        )
        self.webcontroller.start()

        # Create Button Controllers
        self.button_a_controller = ButtonController(self.button_a, "Button A")
        self.button_a_controller.register_event("on_press", self.ledcontroller.on)
        self.button_a_controller.register_event("on_release", self.ledcontroller.off)

        self.button_b_controller = ButtonController(self.button_b, "Button B")
        self.button_b_controller.register_event("on_press", self.ledcontroller.on)
        self.button_b_controller.register_event("on_release", self.ledcontroller.off)

        self.button_c_controller = ButtonController(self.button_c, "Button C")
        self.button_c_controller.register_event("on_press", self.ledcontroller.on)
        self.button_c_controller.register_event("on_release", self.ledcontroller.off)


if __name__ == "__main__":
    admin = Admin()
    logger.info("Program started.")
    mem_alloc = gc.mem_alloc()
    mem_free = gc.mem_free()

    statvfs = os.statvfs(".")
    total_space = statvfs[1] * statvfs[2]
    free_space = statvfs[1] * statvfs[3]

    logger.info(
        f"RAM used: {mem_alloc}/{mem_alloc + mem_free} bytes ({((mem_alloc/(mem_alloc + mem_free))*100):.2f}%)"
    )
    logger.info(
        f"Flash used: {total_space-free_space}/{total_space} bytes ({(((total_space-free_space)/total_space)*100):.2f}%)"
    )
    logger.info("Initializing infinite loop...")
    while True:
        # Process events from Button A
        admin.button_a_controller.process()

        # Process events from Button B
        admin.button_b_controller.process()

        # Process events from Button C
        admin.button_c_controller.process()

        # Process Web server requests
        admin.webcontroller.process()
