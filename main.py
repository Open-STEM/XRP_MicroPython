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
    wlan.disconnect()
    wlan.active(False)

from XRPLib.defaults import *

def print_imu(calibration_time, print_time):
    # Method for testing and tuning gyro calibration
    imu.reset_pitch()
    imu.reset_roll()
    imu.reset_yaw()
    imu.calibrate(calibration_time)
    start_time = time.time()
    while time.time() < start_time + print_time:
        print(f"{calibration_time}, {print_time}, {imu.get_pitch()}, {imu.get_yaw()}, {imu.get_roll()}")
        time.sleep(0.1)