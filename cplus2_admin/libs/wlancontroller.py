import network
import time


class WLANController:
    NETWORK_PROFILES = "wifi.dat"
    AP_SSID = "M5Stack"

    def __init__(self) -> None:
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ap_if.active(True)

    def read_profiles(self):
        with open(self.NETWORK_PROFILES) as f:
            lines = f.readlines()
        profiles = {}
        for line in lines:
            ssid, password = line.strip("\n").split(";")
            profiles[ssid] = password
        return profiles

    def write_profiles(self, profiles):
        lines = []
        for ssid, password in profiles.items():
            lines.append("%s;%s\n" % (ssid, password))
        with open(self.NETWORK_PROFILES, "w") as f:
            f.write("".join(lines))

    def list_available(self):
        available = self.sta_if.scan()
        return available

    def configure_ap(self):
        self.ap_if.config(essid=self.AP_SSID)

    def get_ap_info(self):
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
            print("Connecting to WiFi...", end="")
            self.sta_if.connect(ssid, password)
            for retry in range(200):
                connected = self.sta_if.isconnected()
                if connected:
                    break
                time.sleep(0.2)
                print(".", end="")
            if connected:
                print("\nNetwork config: ", self.sta_if.ifconfig())

    def disconnect(self):
        if self.sta_if.isconnected():
            print("Disconnecting...", end="")
            self.sta_if.disconnect()
        for retry in range(200):
            if not self.sta_if.isconnected():
                break
            time.sleep(0.2)
            print(".", end="")