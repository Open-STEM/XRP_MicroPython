# Getting Starting with your XRP Robot

- First steps of tutorial borrowed from [here](https://projects.raspberrypi.org/en/projects/get-started-pico-w/1)

# Step 1: Install Micropython on your XRP Robot Controller:


### Download the latest version of Raspberry Pi Pico W firmware [here](https://rpf.io/pico-w-firmware)

Connect the small end of your micro USB cable to the Raspberry Pi Pico W.

![](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/pico-top-plug.png)

Hold down the BOOTSEL button on your Raspberry Pi Pico W.

![](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/bootsel.png)

Connect the other end to your desktop computer, laptop, or Raspberry Pi.

![](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/plug-in-pico.png)

Your file manager should open up, with Raspberry Pi Pico being show as an externally connected drive. Drag and drop the firmware file you downloaded into the file manager. Your Raspberry Pi Pico should disconnect and the file manager will close.

![](https://projects-static.raspberrypi.org/projects/get-started-pico-w/0b627b5c80e71000b5116ecc35acaa49094aef84/en/images/file_manager.png)


# Step 2: Installing dev environment (Mu)


### Download the latest version of the Mu editor [here](https://codewith.mu)

Open Mu, and select the RP2040 Option (Or whichever option represents using Micropython for the board you have)

![](https://codewith.mu/img/en/tutorials/mode_selector1-1.png)

## Step 3: Installing the library

Right now installing the library is a little informal. Clone or download the library files through github.

Then, in mu, press load, and navigate to the \_\_init\_\_.py file (or any other in that directory)

Press the "Files" button, and drag the files from your computer into the board's memory.

Use them with ```from [File] import [ClassName]```.

ex. ```from hcsr04 import HCSR04```

____

In the future, installing the library will be a lot easier, using mip (Micropython's package installer). I haven't tested this method yet and so do not have explicit instructions of how to do it.
