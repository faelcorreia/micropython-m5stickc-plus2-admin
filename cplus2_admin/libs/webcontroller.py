from libs.micropyserver import MicroPyServer
from libs.wlancontroller import WLANController
import binascii
import json
from machine import Pin
from libs.st7789 import ST7789
from libs.mpu6886 import MPU6886
from libs.pcf8563 import PCF8563
import libs.colors as colors
import random
import os


class WebController:
    DEFAULT_MESSAGE = "OK"
    DEFAULT_TEXT_X = 10
    DEFAULT_TEXT_Y = 20
    DATA_FOLDER = "/data"

    def __init__(
        self,
        wlancontroller: WLANController,
        backlight: Pin,
        tft: ST7789,
        sensor: MPU6886,
        rtc: PCF8563,
    ) -> None:
        self.micropyserver = MicroPyServer()

        self.wlancontroller = wlancontroller
        self.backlight = backlight
        self.tft = tft
        self.sensor = sensor
        self.rtc = rtc

        # Define routes
        self.micropyserver.add_route("/", self.root)
        self.micropyserver.add_route("/wlans", self.get_wlans)
        self.micropyserver.add_route("/wlan_connect", self.wlan_connect, method="POST")
        self.micropyserver.add_route("/get_ap_info", self.get_ap_info)
        self.micropyserver.add_route("/get_sta_info", self.get_sta_info)
        self.micropyserver.add_route(
            "/toggle_backlight", self.toggle_backlight, method="POST"
        )
        self.micropyserver.add_route(
            "/set_background_color", self.set_background_color, method="POST"
        )
        self.micropyserver.add_route(
            "/set_foreground_color", self.set_foreground_color, method="POST"
        )
        self.micropyserver.add_route("/set_text", self.set_text, method="POST")
        self.micropyserver.add_route("/get_temperature", self.get_temperature)
        self.micropyserver.add_route("/get_gyro", self.get_gyro)
        self.micropyserver.add_route("/get_acceleration", self.get_acceleration)
        self.micropyserver.add_route("/get_rtc_time", self.get_rtc_time)

        # Create data folder
        try:
            os.stat(self.DATA_FOLDER)
        except:
            os.mkdir(self.DATA_FOLDER)

        # Get WLAN profile and connect
        self.wlan_profile_path = f"{self.DATA_FOLDER}/wlan_profile.json"
        try:
            with open(self.wlan_profile_path, "r") as f:
                wlan_profile = json.load(f)
                wlancontroller.connect(wlan_profile["ssid"], wlan_profile["password"])
        except:
            print("Default WLAN to connect does not exists.")
        ap_info = wlancontroller.get_ap_info()

        # Start default screen
        self.bg_color = colors.BLACK
        self.fg_color = colors.WHITE
        self.backlight.on()
        self.tft.fill(self.bg_color)
        tft.text(
            "AP SSID:",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y,
            self.fg_color,
            self.bg_color,
        )
        tft.text(
            ap_info["ssid"],
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y + 20,
            self.fg_color,
            self.bg_color,
        )
        tft.text(
            "AP IP:",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y + 50,
            self.fg_color,
            self.bg_color,
        )
        tft.text(
            ap_info["ip"],
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y + 70,
            self.fg_color,
            self.bg_color,
        )

    def parse_http_request(self, request_text):
        headers_section, body = request_text.split("\r\n\r\n", 1)
        lines = headers_section.split("\r\n")
        request_line = lines[0]
        headers = {}
        for line in lines[1:]:
            if line:
                key, value = line.split(": ", 1)
                headers[key] = value
        return {"headers": headers, "body": body}

    def root(self, request_text):
        with open("public/index.html") as f:
            self.micropyserver.send(f.read())

    def get_ap_info(self, request_text):
        ap_info = self.wlancontroller.get_ap_info()
        self.micropyserver.send(json.dumps(ap_info))

    def get_sta_info(self, request_text):
        sta_info = self.wlancontroller.get_sta_info()
        self.micropyserver.send(json.dumps(sta_info))

    def get_wlans(self, request_text):
        wlans = []
        for wlan in self.wlancontroller.list_available():
            wlans.append(
                {
                    "ssid": wlan[0].decode(),
                    "bssid": binascii.hexlify(wlan[1]).decode(),
                    "channel": wlan[2],
                    "dbm": wlan[3],
                    "is_open": wlan[4] == 0,
                }
            )
        self.micropyserver.send(json.dumps(wlans))

    def wlan_connect(self, request_text):
        request = self.parse_http_request(request_text)
        wlan_data = json.loads(request["body"])
        try:
            self.wlancontroller.disconnect()
            self.wlancontroller.connect(wlan_data["ssid"], wlan_data["password"])
            with open(self.wlan_profile_path, "w") as f:
                json.dump(wlan_data, f)
            self.micropyserver.send(self.DEFAULT_MESSAGE)
        except Exception as e:
            print(e)
            self.micropyserver.send(str(e))

    def toggle_backlight(self, request_text):
        if self.backlight.value() == 1:
            self.backlight.off()
        else:
            self.backlight.on()
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_background_color(self, request_text):
        request = self.parse_http_request(request_text)
        rgb = json.loads(request["body"])
        self.bg_color = colors.rgb565(rgb["r"], rgb["g"], rgb["b"])
        self.tft.fill(self.bg_color)
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_foreground_color(self, request_text):
        request = self.parse_http_request(request_text)
        rgb = json.loads(request["body"])
        self.fg_color = colors.rgb565(rgb["r"], rgb["g"], rgb["b"])
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_text(self, request_text):
        request = self.parse_http_request(request_text)
        text = json.loads(request["body"])["text"]
        self.tft.fill(self.bg_color)
        self.tft.text(
            text, self.DEFAULT_TEXT_X, self.DEFAULT_TEXT_Y, self.fg_color, self.bg_color
        )
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def get_temperature(self, request_text):
        self.micropyserver.send(json.dumps({"temperature": self.sensor.temperature()}))

    def get_gyro(self, request_text):
        gyro = self.sensor.gyro
        self.micropyserver.send(
            json.dumps({"gyro_x": gyro[0], "gyro_y": gyro[1], "gyro_z": gyro[2]})
        )

    def get_acceleration(self, request_text):
        acceleration = self.sensor.acceleration
        self.micropyserver.send(
            json.dumps(
                {
                    "acceleration_x": acceleration[0],
                    "acceleration_y": acceleration[1],
                    "acceleration_z": acceleration[2],
                }
            )
        )

    def start(self):
        self.micropyserver.start()

    def process(self):
        self.micropyserver.process()

    def get_rtc_time(self, request_text):
        datetime = self.rtc.datetime()
        self.micropyserver.send(
            json.dumps(
                {
                    "year": datetime[0],
                    "month": datetime[1],
                    "day": datetime[2],
                    "hour": datetime[3],
                    "minute": datetime[4],
                    "second": datetime[5],
                    "weekday": datetime[6],
                }
            )
        )
