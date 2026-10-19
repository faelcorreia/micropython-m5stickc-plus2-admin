"""
MIT license
Copyright (c) 2024 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from libs.audio.buzzercontroller import BuzzerController
from libs.audio.microphonecontroller import MicrophoneController
from libs.network.wlancontroller import WLANController
from libs.led.ledcontroller import LEDController
import binascii
import json
from machine import Pin, PWM # type: ignore
from libs.display.st7789 import ST7789
from libs.sensor.mpu6886 import MPU6886
from libs.rtc.pcf8563 import PCF8563
from libs.button.buttoncontroller import ButtonController
from libs.power.batterycontroller import BatteryController
from libs.system.systemcontroller import SystemController
import libs.display.colors as colors
import os
import libs.network.tinyweb as tinyweb
from libs.network.tinyweb import response, request
import libs.std.logging as logging
import libs.std.time as time
from libs.display.bitmap import Bitmap

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
        self.config[key] = value
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f)
            return True
        except OSError:
            return False

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
        buzzercontroller: BuzzerController,
        microphonecontroller: MicrophoneController = None,
        batterycontroller: BatteryController = None,
        systemcontroller: SystemController = None,
        buttons: dict = None,
        i2c = None,
    ) -> None:
        self.logger: logging.Logger = logging.getLogger("WEBCONTROLLER")
        self.app = tinyweb.webserver(debug=True, request_timeout=10)

        self.wlancontroller = wlancontroller
        self.ledcontroller = ledcontroller
        self.backlight = backlight
        self.display = display
        self.sensor = sensor
        self.rtc = rtc
        self.buzzercontroller = buzzercontroller
        self.microphonecontroller = microphonecontroller
        self.batterycontroller = batterycontroller
        self.systemcontroller = systemcontroller
        self.buttons = buttons or {}
        self.i2c = i2c
        
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
        if wlan_ssid is not None:
            wlancontroller.connect(wlan_ssid, wlan_password)
        else:
            self.logger.warning("Default WLAN to connect does not exist.")
            
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
            f"AP SSID: {ap_info['ssid']}",
            self.DEFAULT_TEXT_X,
            self.DEFAULT_TEXT_Y,
            self.display_parameters["foreground_color"],
            self.display_parameters["background_color"],
        )
        display.text(
            f"AP IP: {ap_info['ip']}",
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
        self.app.add_resource(WebController.Buzzer, "/api/buzzer", buzzercontroller=self.buzzercontroller)
        self.app.add_resource(WebController.BuzzerStop, "/api/buzzer/stop", buzzercontroller=self.buzzercontroller)
        self.app.add_resource(WebController.Microphone, "/api/microphone/level", microphonecontroller=self.microphonecontroller)
        self.app.add_resource(WebController.Sensor, "/api/sensor", sensor=self.sensor)
        self.app.add_resource(WebController.SensorCalibrate, "/api/sensor/calibrate", sensor=self.sensor)
        self.app.add_resource(WebController.Battery, "/api/battery", batterycontroller=self.batterycontroller)
        self.app.add_resource(WebController.System, "/api/system", systemcontroller=self.systemcontroller, buttons=self.buttons)
        self.app.add_resource(WebController.Buttons, "/api/buttons", buttons=self.buttons)
        self.app.add_resource(WebController.I2CScan, "/api/i2c/scan", i2c=self.i2c)
        self.app.add_resource(WebController.I2CRead, "/api/i2c/read", i2c=self.i2c)

    @staticmethod
    def button_states(buttons: dict) -> dict:
        states = {}
        for name, button in buttons.items():
            states[name] = {
                "state": button.state,
                "pressed": button.is_pressed,
            }
        return states

    def start(self):
        self.app.run(host='0.0.0.0', port=80, loop_forever=False)
        
    async def stop_coro(self):
        self.app.loop.stop()
        
    async def stop(self):
        return await self.stop_coro()

    def process(self):
        # Run one iteration of the asyncio loop. tinyweb keeps its server
        # coroutine alive as a task, so stopping the loop after a single
        # slice is enough to service pending requests without blocking the
        # button and buzzer processing in the main loop.
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
            if not ssid:
                return {"message": "SSID is required.", "result": None}, 400

            previous_ssid = config.get_property("wlan_ssid")
            previous_password = config.get_property("wlan_password")

            wlancontroller.disconnect()
            if wlancontroller.connect(ssid, password):
                config.set_property("wlan_ssid", ssid)
                config.set_property("wlan_password", password)
                return {"message": "connected", "result": None}, 200

            # Restore the previous network so the admin page stays reachable.
            if previous_ssid:
                wlancontroller.connect(previous_ssid, previous_password)
            return {"message": "Wrong ssid or password.", "result": None}, 400
    
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

    class Sensor:
        """Combined sample used by the 3D visualization.

        ``ticks_ms`` lets the browser integrate the gyro using the device's
        own clock instead of the (jittery) network arrival time.
        """
        def get(self, data, sensor: MPU6886):
            del data
            acceleration, gyro, temperature = sensor.sample()
            result = {
                "accel": {
                    "x": acceleration[0],
                    "y": acceleration[1],
                    "z": acceleration[2],
                },
                "gyro": {
                    "x": gyro[0],
                    "y": gyro[1],
                    "z": gyro[2],
                },
                "temperature": temperature,
                "units": {
                    "accel": "g",
                    "gyro": "deg/s",
                    "temperature": "C",
                },
                "ticks_ms": time.ticks_ms(),
            }
            return {"message": "Sensor sample returned.", "result": result}

    class SensorCalibrate:
        def post(self, data, sensor: MPU6886):
            del data
            offsets = sensor.calibrate()
            return {
                "message": "Gyro calibrated.",
                "result": {
                    "x": offsets[0],
                    "y": offsets[1],
                    "z": offsets[2],
                },
            }

    class Battery:
        def get(self, data, batterycontroller: BatteryController):
            del data
            return {
                "message": "Battery status returned.",
                "result": batterycontroller.read(),
            }

    class System:
        def get(self, data, systemcontroller: SystemController, buttons: dict):
            del data
            result = systemcontroller.info()
            result["buttons"] = WebController.button_states(buttons)
            return {"message": "System info returned.", "result": result}

    class Buttons:
        def get(self, data, buttons: dict):
            del data
            return {
                "message": "Button states returned.",
                "result": WebController.button_states(buttons),
            }

    class I2CScan:
        def get(self, data, i2c):
            del data
            addresses = []
            if i2c is not None:
                for address in range(0x08, 0x78):
                    try:
                        i2c.readfrom(address, 1)
                        addresses.append(address)
                    except OSError:
                        pass
            return {
                "message": "I2C scan finished.",
                "result": {"addresses": addresses},
            }

    class I2CRead:
        """Read registers from an I2C device (useful for external sensors).

        Example: /api/i2c/read?address=0x68&register=0x75&length=1
        """
        def get(self, data, i2c):
            if i2c is None:
                return {"message": "I2C bus is not available.", "result": None}, 400
            try:
                address = int(data.get("address", "0"), 0)
                register = int(data.get("register", "0"), 0)
                length = int(data.get("length", "1"))
            except (TypeError, ValueError):
                return {"message": "Invalid address, register or length.", "result": None}, 400

            if not (0x08 <= address < 0x78) or not (0 <= register <= 0xFF):
                return {"message": "Address or register out of range.", "result": None}, 400
            if not (1 <= length <= 32):
                return {"message": "Length must be between 1 and 32.", "result": None}, 400

            try:
                values = i2c.readfrom_mem(address, register, length)
            except OSError as error:
                return {
                    "message": f"I2C read failed: {error}",
                    "result": None,
                }, 400

            return {
                "message": "I2C data returned.",
                "result": {
                    "address": address,
                    "register": register,
                    "data": list(values),
                },
            }

    class LED:
        def get(self, data, ledcontroller: LEDController):
            del data
            ledcontroller.toggle()
            return {"message": "LED toggled.", "result": None}
        
    class Buzzer:
        def get(self, data, buzzercontroller: BuzzerController):
            del data
            return {
                "message": "Buzzer status returned.",
                "result": {
                    "playing": buzzercontroller.is_playing(),
                    "remaining_ms": buzzercontroller.remaining_ms(),
                },
            }

        def post(self, data, buzzercontroller: BuzzerController):
            try:
                bpm: int = data["bpm"]
                step: int = data["step"]
                notes: list[str] = data["notes"]
                count = buzzercontroller.play_notes(bpm, step, notes)
                return {
                    "message": f"Playing {count} notes.",
                    "result": {"notes": count},
                }, 200
            except Exception as e:
                return {
                    "message": f"Exception while playing notes: {str(e)}.",
                    "result": None,
                }, 400

    class BuzzerStop:
        def get(self, data, buzzercontroller: BuzzerController):
            del data
            buzzercontroller.stop()
            return {"message": "Buzzer stopped.", "result": None}

        def post(self, data, buzzercontroller: BuzzerController):
            del data
            buzzercontroller.stop()
            return {"message": "Buzzer stopped.", "result": None}

    class Microphone:
        def get(self, data, microphonecontroller: MicrophoneController):
            if microphonecontroller is None or not microphonecontroller.available:
                return {
                    "message": (
                        "I2S.PDM_RX is not available in this firmware. "
                        "See firmware/pdm_rx/README.md for the custom build."
                    ),
                    "result": None,
                }, 503
            try:
                samples = int(data.get("samples", MicrophoneController.DEFAULT_SAMPLES))
                return {
                    "message": "Microphone level returned.",
                    "result": microphonecontroller.level(samples),
                }
            except Exception as error:
                return {
                    "message": f"Could not read the microphone: {error}",
                    "result": None,
                }, 500
                
            
