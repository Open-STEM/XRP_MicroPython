# Getting Starting with your XRP Robot

- First steps of tutorial borrowed from [here](https://projects.raspberrypi.org/en/projects/get-started-pico-w/1)

# Step 1: Install Micropython on your XRP Robot Controller:


### Download the latest version of Raspberry Pi Pico W firmware [here](https://rpf.io/pico-w-firmware)

Connect the small end of your micro USB cable to the Raspberry Pi Pico W.

![A Raspberry Pi Pico W connected to the small end of a micro USB cable.](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/pico-top-plug.png)

Hold down the BOOTSEL button on your Raspberry Pi Pico W.

![A Raspberry Pi Pico W with the BOOTSEL button highlighted](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/bootsel.png)

Connect the other end to your desktop computer, laptop, or Raspberry Pi.

![A Raspberry Pi Pico W connected to a laptop via a micro USB cable.](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/plug-in-pico.png)

Your file manager should open up, with Raspberry Pi Pico being show as an externally connected drive. Drag and drop the firmware file you downloaded into the file manager. Your Raspberry Pi Pico should disconnect and the file manager will close.

![Image of the Windows file manager opened, showing Raspberry Pi Pico connected as an external drive](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/file_manager.png)


# Step 2: Installing dev environment (Mu)


### Download the latest version of the Mu editor [here](https://codewith.mu)

Open Mu, and select the RP2040 Option (Or whichever option represents using Micropython for the board you have)

![](https://codewith.mu/img/en/tutorials/mode_selector1-1.png)

## Step 3: Installing the library using mip

Open up a new file in mu.

Copy the following code into that file:

```python
import network
import mip
import time

def install_update_library(wifi_ssid, wifi_password, timeout = 5):
    
    wlan = network.WLAN(network.STA_IF)
    # Configure board to connect to wifi
    wlan.active(True)
    wlan.connect(wifi_ssid,wifi_password)
    start_time = time.time()
    # Wait until connection is confirmed before attempting install
    while not wlan.isconnected():
            print("Connecting to network, may take a second")
            if time.time() > start_time+timeout:
                print("Failed to connect to network, please try again")
                wlan.disconnect()
                return
            time.sleep(0.25)
    # Install up-to-date library files and dependencies
    mip.install("github:Open-STEM/XRP_MicroPython")
    # Disconnect and disable wifi, since it is no longer needed
    wlan.disconnect()
    wlan.active(False)
    
install_update_library("your-ssid","your-password")
```

Edit the method call at the bottom to include your wifi's details, then hit run.

Check the Serial Monitor to confirm that the libraries were properly installed.