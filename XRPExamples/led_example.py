from XRPLib.board import Board
from machine import Timer, Pin
import time

# Get a reference to the board
board = Board.get_default_board()

# Create a timer for the RGB LED, assuming it's present on this board
rgb_led_timer = Timer(-1)

# Conversion from hue to RGB
def hue_to_rgb(hue):
    # Initialize RGB values
    r = 0
    g = 0
    b = 0
    
    # Ensure hue is in range of [0,360)
    hue %= 360
    
    if(hue < 120):
        # Red to green region
        r = (120 - hue) / 120 * 255
        g = (hue -   0) / 120 * 255
        b = 0
    elif(hue < 240):
        # Green to blue region
        hue -= 120
        r = 0
        g = (120 - hue) / 120 * 255
        b = (hue -   0) / 120 * 255
    else:
        # Blue to red region
        hue -= 240
        r = (hue -   0) / 120 * 255
        g = 0
        b = (120 - hue) / 120 * 255
    
    # Return RGB as tuple of integers in range of [0,255]
    return (int(r), int(g), int(b))

def update_rgb_led_rainbow(timer):
    # Set hue based on current time. Hue is an angle up to 360 degrees,
    # so using the milliseconds divided by 10 creates a rainbow that
    # repeats every 3.6 seconds
    hue = time.ticks_ms() / 10
    
    # Compute RGB values
    rgb = hue_to_rgb(hue)
    
    # Max brightness is blinding, so recompute RGB values with 10% brightness
    brightness = 0.1
    r = int(rgb[0] * brightness)
    g = int(rgb[1] * brightness)
    b = int(rgb[2] * brightness)
    
    # Set the RGB LED color
    board.set_rgb_led(r, g, b)

def start_led_demo():
    # Make the monochrome LED start blinking
    board.led_blink(1)
    
    # If this board has an RGB LED, make it start changing colors
    if hasattr(Pin.board, "BOARD_NEOPIXEL"):
        # Set up timer to update the RGB LED at 100Hz for smooth color changes
        rgb_led_timer.init(freq = 100, callback = update_rgb_led_rainbow)

def stop_led_demo():
    # Make the monochrome LED stop blinking and turn off the LED
    board.led_blink(0)
    board.led_off()
    
    # If this board has an RGB LED, stop the timer and turn off the LED
    if hasattr(Pin.board, "BOARD_NEOPIXEL"):
        rgb_led_timer.deinit()
        board.set_rgb_led(0, 0, 0)

start_led_demo()