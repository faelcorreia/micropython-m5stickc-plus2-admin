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

from libs.wlancontroller import WLANController
from libs.ledcontroller import LEDController
import binascii
import json
from machine import Pin # type: ignore
from libs.st7789 import ST7789
from libs.mpu6886 import MPU6886
from libs.pcf8563 import PCF8563
import libs.colors as colors
import os
import libs.tinyweb as tinyweb
from libs.tinyweb import response, request
import libs.logging as logging
from libs.bitmap import Bitmap

class Config():
    def __init__(self, config_path):
        self.config_path = config_path
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except:
            self.config = {}
    
    def get_property(self, key):
        return self.config.get(key)
    
    def set_property(self, key, value):
        if key in self.config:
            self.config["key"] = value
            with open(self.config_path, "w") as f:
                json.dump(self.config, f)

class WebController:
    DEFAULT_MESSAGE = "OK"
    DEFAULT_TEXT_X = 10
    DEFAULT_TEXT_Y = 20
    DATA_FOLDER = "/data"
    CHUNK_SIZE = 1024

    def __init__(
        self,
        wlancontroller: WLANController,
        ledcontroller: LEDController,
        backlight: Pin,
        display: ST7789,
        sensor: MPU6886,
        rtc: PCF8563,
    ) -> None:
        self.logger: logging.Logger = logging.getLogger("WEBCONTROLLER")
        self.app = tinyweb.webserver(debug=True, request_timeout=10)
        
        self.wlancontroller = wlancontroller
        self.ledcontroller = ledcontroller
        self.backlight = backlight
        self.display = display
        self.sensor = sensor
        self.rtc = rtc
        
        # Create data folder
        try:
            os.stat(self.DATA_FOLDER)
        except:
            os.mkdir(self.DATA_FOLDER)
        
        # Config file
        config_path = f"{self.DATA_FOLDER}/config.json"
        self.config = Config(config_path)
        
        # Get WLAN profile and connect
        wlan_ssid = self.config.get_property("wlan_ssid")
        wlan_password = self.config.get_property("wlan_password")
        if wlan_ssid != None and wlan_password != None:
            wlancontroller.connect(wlan_ssid, wlan_password)        
        else:
            self.logger.warning("Default WLAN to connect does not exists.")
            
        # LCD Parameters
        self.display
        self.display_parameters = {
            "background_color" : colors.BLACK,
            "foreground_color" : colors.WHITE,
            "background_image" : None,
            "text_x" : self.DEFAULT_TEXT_X,
            "text_y" : self.DEFAULT_TEXT_Y
        }
        
        # Start default screen
        ap_info = wlancontroller.get_ap_info()
        self.backlight.on()
        self.display.fill(self.display_parameters["background_color"])
        display.text(
            f"AP SSID: {ap_info["ssid"]}",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y,
            self.display_parameters["foreground_color"],
            self.display_parameters["background_color"],
        )
        display.text(
            f"AP IP: {ap_info["ip"]}",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y + 10,
            self.display_parameters["foreground_color"],
            self.display_parameters["background_color"],
        )

        # Define routes
        self.app.add_route("/", self.root)
        self.app.add_resource(WebController.AP, "/api/ap", wlancontroller=self.wlancontroller)
        self.app.add_resource(WebController.STA, "/api/sta", wlancontroller=self.wlancontroller)
        self.app.add_resource(WebController.WLANList, "/api/wlan", wlancontroller=self.wlancontroller)
        self.app.add_resource(WebController.WLANConnect, "/api/wlan/connect", wlancontroller=self.wlancontroller, config=self.config)
        self.app.add_resource(WebController.RTC, "/api/rtc", rtc=self.rtc)
        self.app.add_resource(WebController.DisplayBacklight, "/api/display/backlight/toggle", backlight=self.backlight)
        self.app.add_resource(WebController.DisplayBackgroundColor, "/api/display/background/color", display=self.display, display_parameters=self.display_parameters)
        self.app.add_resource(WebController.DisplayBackgroundImage, "/api/display/background/image", max_body_size=200000, display=self.display, display_parameters=self.display_parameters)
        self.app.add_resource(WebController.DisplayForegroundColor, "/api/display/foreground/color", display_parameters=self.display_parameters)
        self.app.add_resource(WebController.DisplayText, "/api/display/text", display=self.display, display_parameters=self.display_parameters)
        self.app.add_resource(WebController.SensorTemperature, "/api/sensor/temperature", sensor=self.sensor)
        self.app.add_resource(WebController.SensorRotation, "/api/sensor/rotation", sensor=self.sensor)
        self.app.add_resource(WebController.SensorAcceleration, "/api/sensor/acceleration", sensor=self.sensor)
        self.app.add_resource(WebController.LED, "/api/led/toggle", ledcontroller=self.ledcontroller)

    def start(self):
        self.app.run(host='0.0.0.0', port=8081, loop_forever=False)
        
    async def stop_coro(self):
        self.app.loop.stop()
        
    async def stop(self):
        return await self.stop_coro()

    def process(self):
        self.app.loop.create_task(self.stop())
        self.app.loop.run_forever()

    async def root(self, req: request, resp: response):
        del req
        await resp.start_html()
        with open("public/index.html") as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                await resp.send(data)
                
    class AP:
        def get(self, data, wlancontroller: WLANController):
            del data
            ap = wlancontroller.get_ap_info()
            return {"message": "AP info returned.", "result": ap}
        
    class STA:
        def get(self, data, wlancontroller: WLANController):
            del data
            sta = wlancontroller.get_sta_info()
            return {"message": "STA info returned.", "result": sta}

    class WLANList:
        def get(self, data, wlancontroller: WLANController):
            del data
            wlans = []
            for wlan in wlancontroller.list_available():
                wlans.append(
                    {
                        "ssid": wlan[0].decode(),
                        "bssid": binascii.hexlify(wlan[1]).decode(),
                        "channel": wlan[2],
                        "dbm": wlan[3],
                        "is_open": wlan[4] == 0,
                    }
                )
            return {"message": "WLAN list returned.", "result": wlans}
        
    class WLANConnect:
        def post(self, data:dict, wlancontroller: WLANController, config: Config):  
            ssid = data.get("ssid")
            password = data.get("password")
            if ssid != None and password != None:
                wlancontroller.disconnect()            
                connected = wlancontroller.connect(data["ssid"], data["password"])
                if connected:
                    config.set_property("wlan_ssid", data["ssid"])
                    config.set_property("wlan_password", data["password"])
                    return {'message': 'connected', 'result': None}, 200
                else:
                    wlancontroller.connect(config.get_property("wlan_ssid"), config.get_property("wlan_password"))
            return {'message': 'Wrong ssid or password.', 'result' : None}, 400
    
    class RTC:
        def get(self, data, rtc: PCF8563):
            del data
            datetime = rtc.datetime()
            result = {
                "year": datetime[0],
                "month": datetime[1],
                "day": datetime[2],
                "hour": datetime[3],
                "minute": datetime[4],
                "second": datetime[5],
                "weekday": datetime[6],
            }
            return {"message" : "RTC datetime returned.", "result" : result}
                
        def post(self, data, rtc: PCF8563):
            rtc.datetime((data["year"], data["month"], data["day"], data["hour"], data["minute"], data["second"], data["weekday"]))
            return {"message": "RTC datetime altered.", "result": None}   

    class DisplayBacklight:
        def get(self, data, backlight: Pin):
            del data
            if backlight.value() == 1:
                backlight.off()
            else:
                backlight.on()
            return {"message": "Backlight toggled.", "result" : None}
        
    class DisplayBackgroundColor:
        def post(self, data, display: ST7789, display_parameters: dict):
            display_parameters["background_color"] = colors.rgb565(data["r"], data["g"], data["b"])
            display.fill(display_parameters["background_color"])
            display_parameters["background_image"] = None
            return {"message" : "Background color changed.", "result": None}
        
    class DisplayBackgroundImage:
        def post(self, data, display: ST7789, display_parameters: dict):
            bitmap_base64 = data["file"]
            pixels = Bitmap.extract_pixels_from_base64bitmap(bitmap_base64)
            display.image(pixels)
            display_parameters["background_image"] = pixels
            return {"message" : "Background image changed.", "result": None}
        
    class DisplayForegroundColor:
        def post(self, data, display_parameters: dict):
            display_parameters["foreground_color"] = colors.rgb565(data["r"], data["g"], data["b"])
            return {"message": "Foreground color changed.", "result": None}
        
    class DisplayText:
        def post(self, data, display: ST7789, display_parameters: dict):
            if display_parameters["background_image"]:
                display.image(display_parameters["background_image"])
            else:
                display.fill(display_parameters["background_color"])
            display.text(
                data["text"], display_parameters["text_x"], display_parameters["text_y"], display_parameters["foreground_color"], display_parameters["background_color"]
            )
            return {"message" : "Text written.", "result": None}
    
    class SensorTemperature:
        def get(self, data, sensor: MPU6886):
            del data
            temperature = {"temperature":sensor.temperature}
            return {"message": "Sensor temperature returned.", "result" : temperature}

    class SensorRotation:
        def get(self, data, sensor: MPU6886):
            del data
            gyro = sensor.gyro
            rotation = {"x": gyro[0], "y": gyro[1], "z": gyro[2]}
            return {"message" : "Sensor rotation data returned.", "result" : rotation}
        
    class SensorAcceleration:
        def get(self, data, sensor: MPU6886):
            del data
            acceleration = sensor.acceleration
            acceleration_data = {
                "x": acceleration[0],
                "y": acceleration[1],
                "z": acceleration[2]
            }
            return {"message" : "Sensor acceleration data returned.", "result": acceleration_data}

    class LED:
        def get(self, data, ledcontroller: LEDController):
            del data
            ledcontroller.toggle()
            return {"message": "LED toggled.", "result": None}
