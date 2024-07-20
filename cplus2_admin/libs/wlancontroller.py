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

import network  # type: ignore
import time


class WLANController:
    AP_SSID = "M5StickC"
    CONNECT_TIMEOUT = 30
    CONNECT_DELAY = 0.2

    def __init__(self) -> None:
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ap_if.active(True)

    def list_available(self):
        available = self.sta_if.scan()
        return available

    def configure_ap(self):
        self.ap_if.config(essid=self.AP_SSID)

    def get_ap_info(self) -> dict[str, str]:
        ap_info = self.ap_if.ifconfig()
        return {
            "ssid": self.AP_SSID,
            "ip": ap_info[0],
            "netmask": ap_info[1],
            "dns1": ap_info[2],
            "dns2": ap_info[3],
        }

    def get_sta_info(self):
        if self.sta_if.isconnected():
            sta_info = self.sta_if.ifconfig()
            return {
                "ssid": self.sta_ssid,
                "ip": sta_info[0],
                "netmask": sta_info[1],
                "dns1": sta_info[2],
                "dns2": sta_info[3],
            }
        return None

    def connect(self, ssid, password):
        if not self.sta_if.isconnected():
            self.sta_ssid = ssid
            print("Connecting to WLAN...\n")
            self.sta_if.connect(ssid, password)
            retries = self.CONNECT_TIMEOUT / self.CONNECT_DELAY
            for _ in range(retries):
                connected = self.sta_if.isconnected()
                if connected:
                    break
                time.sleep(self.CONNECT_DELAY)
            if connected:
                print("Connected. Network config: ", self.sta_if.ifconfig())
                return True
        return False

    def disconnect(self):
        if self.sta_if.isconnected():
            print("Disconnecting from WLAN...\n")
            self.sta_if.disconnect()
        retries = self.CONNECT_TIMEOUT / self.CONNECT_DELAY
        for _ in range(retries):
            if not self.sta_if.isconnected():
                break
            time.sleep(self.CONNECT_DELAY)
        print("Disconnected.")
