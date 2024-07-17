from machine import I2C, Pin, SPI, ADC
from libs.st7789 import ST7789, ColorMode_16bit
from libs.pcf8563 import PCF8563
from libs.mpu6886 import MPU6886, SF_G, SF_DEG_S
from libs.wlancontroller import WLANController
from libs.webcontroller import WebController


class Main:
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
    tft = ST7789(
        spi,
        135,
        240,
        reset=Pin(12, Pin.OUT),
        dc=Pin(14, Pin.OUT),
        cs=Pin(5, Pin.OUT),
        buf=bytearray(4096),
        color_mode=ColorMode_16bit,
    )

    # Set up MPU6886 Sensor
    sensor = MPU6886(i2c, accel_sf=SF_G, gyro_sf=SF_DEG_S)

    def on_button_press(self, button: Pin):
        temp_state = button.value()
        # OnRelease
        if (self.last_button_state == 0) and (temp_state == 1):
            self.last_button_state = temp_state
            self.led.value(0)
        # OnDown
        elif (self.last_button_state == 1) and (temp_state == 1):
            self.last_button_state = temp_state
            self.led.value(0)
        # OnPress
        elif (self.last_button_state == 1) and (temp_state == 0):
            self.last_button_state = temp_state
            self.led.value(1)
        # OnUp
        else:
            self.led.value(1)

    def create_network(self):
        self.wlancontroller = WLANController()
        self.wlancontroller.configure_ap()

        self.webcontroller = WebController(
            self.wlancontroller, self.backlight, self.tft, self.sensor, self.rtc
        )
        self.webcontroller.start()


print("Program started.")
print("Initializing infinite loop...\n")

if __name__ == "__main__":
    main = Main()
    main.create_network()
    while True:
        # Button test
        main.on_button_press(main.button_a)

        # Process Web server requests
        main.webcontroller.process()
