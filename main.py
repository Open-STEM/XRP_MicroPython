import network
import mip
import time

def install_update_library(wifi_ssid, wifi_password, timeout = 5):
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True) # configure board to connect to wifi
    wlan.connect(wifi_ssid,wifi_password)
    start_time = time.time()
    while not wlan.isconnected():
            print("Connecting to network, may take a second")
            if time.time() > start_time+timeout:
                print("Failed to connect to network, please try again")
                wlan.disconnect()
                return
            time.sleep(0.25)
    mip.install("github:Open-STEM/XRP_MicroPython")
    mip.install("github:pimoroni/phew")
    wlan.disconnect()
    wlan.active(False)
