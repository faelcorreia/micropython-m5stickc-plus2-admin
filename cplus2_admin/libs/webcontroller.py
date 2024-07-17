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

from libs.micropyserver import MicroPyServer
from libs.wlancontroller import WLANController
import binascii
import json
from machine import Pin # type: ignore
from libs.st7789 import ST7789
from libs.mpu6886 import MPU6886
from libs.pcf8563 import PCF8563
import libs.colors as colors
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
        self.micropyserver.add_route("/set_rtc_time", self.set_rtc_time, method="POST")
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
            f"AP SSID: {ap_info["ssid"]}",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y,
            self.fg_color,
            self.bg_color,
        )
        tft.text(
            f"AP IP: {ap_info["ip"]}",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y + 10,
            self.fg_color,
            self.bg_color,
        )

    def start(self):
        self.micropyserver.start()

    def process(self):
        self.micropyserver.process()

    def root(self, request):
        del request
        with open("public/index.html") as f:
            self.micropyserver.send(f.read())

    def get_ap_info(self, request):
        del request
        ap_info = self.wlancontroller.get_ap_info()
        self.micropyserver.send(json.dumps(ap_info))

    def get_sta_info(self, request):
        del request
        sta_info = self.wlancontroller.get_sta_info()
        self.micropyserver.send(json.dumps(sta_info))

    def get_wlans(self, request):
        del request
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

    def wlan_connect(self, request):
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

    def toggle_backlight(self, request):
        del request
        if self.backlight.value() == 1:
            self.backlight.off()
        else:
            self.backlight.on()
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_background_color(self, request):
        rgb = json.loads(request["body"])
        self.bg_color = colors.rgb565(rgb["r"], rgb["g"], rgb["b"])
        self.tft.fill(self.bg_color)
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_foreground_color(self, request):
        rgb = json.loads(request["body"])
        self.fg_color = colors.rgb565(rgb["r"], rgb["g"], rgb["b"])
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def set_text(self, request):
        text = json.loads(request["body"])["text"]
        self.tft.fill(self.bg_color)
        self.tft.text(
            text, self.DEFAULT_TEXT_X, self.DEFAULT_TEXT_Y, self.fg_color, self.bg_color
        )
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def get_temperature(self, request):
        del request
        self.micropyserver.send(json.dumps({"temperature": self.sensor.temperature()}))

    def get_gyro(self, request):
        del request
        gyro = self.sensor.gyro
        self.micropyserver.send(
            json.dumps({"gyro_x": gyro[0], "gyro_y": gyro[1], "gyro_z": gyro[2]})
        )

    def get_acceleration(self, request):
        del request
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
        
    def set_rtc_time(self, request):
        rtc_time = json.loads(request["body"])
        self.rtc.datetime((rtc_time["year"], rtc_time["month"], rtc_time["day"], rtc_time["hour"], rtc_time["minute"], rtc_time["second"], rtc_time["weekday"]))
        self.micropyserver.send(self.DEFAULT_MESSAGE)

    def get_rtc_time(self, request):
        del request
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
