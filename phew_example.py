from phew import server, template, logging, access_point, dns
from phew.template import render_template
from phew.server import redirect
import gc
import network
import time

class Wifi:

    def __init__(self, network_timeout:int=10):
        gc.threshold(50000) # garbage collection
        self.DOMAIN = "remote.xrp"
        self.timeout = network_timeout
        self.logged_data = {}
        self.buttons = {"forwardButton":    lambda: logging.debug("Button not initialized"),
                        "backwardButton":   lambda: logging.debug("Button not initialized"),
                        "leftButton":       lambda: logging.debug("Button not initialized"),
                        "rightButton":      lambda: logging.debug("Button not initialized"),
                        "stopButton":       lambda: logging.debug("Button not initialized")}
        self.FUNCTION_PREFIX = "startfunction"
        self.FUNCTION_SUFFIX = "endfunction"
        self.display_arrows = False

    def connect_to_network(self, ssid:str, password:str=None):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(ssid, password)
        start_time = time.time()
        while not self.wlan.isconnected():
            print("Connecting to network, may take a second")
            if time.time() > start_time+self.timeout:
                print("Failed to connect to network, please try again")
                self.wlan.disconnect()
                return
            time.sleep(0.25)
        print("Successfully connected to network")

    def start_server(self, robot_number:int):
        self.access_point = access_point(f"XRP_{robot_number}")
        self.ip = network.WLAN(network.AP_IF).ifconfig()[0]
        logging.info(f"Starting DNS Server at {self.ip}")
        dns.run_catchall(self.ip)
        server.run()
        logging.info("Webserver Started")

    def index_page(self, request):
        """ Render index page and respond to form requests """
        if request.method == 'GET':
            return self._generateHTML()
        if request.method == 'POST':
            text = list(request.form.keys())[0]
            self._handleUserFunctionRequest(text)
            return self._generateHTML()

    def wrong_host_redirect(self, request):
        # Captive portal redirects any other host request to self.DOMAIN
        body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://"+self.DOMAIN+"'/ /></head>"
        logging.info("Redirecting to https://"+self.DOMAIN+"/")
        return body

    def hotspot(self, request):
        """ Redirect to Index Page """
        return self._generateHTML()

    def catch_all(self, request):
        """ Catch all requests and redirect if necessary """
        if request.headers.get("host") != self.DOMAIN:
            return redirect("http://"+self.DOMAIN+"/wrong-host-redirect")
        return self.index_page(request=request)
        
    def log_data(self, label:str, data:str):
        self.logged_data[label] = data

    def add_button(self, button_name:str, function):
        self.buttons[button_name] = function

    def registerForwardButton(self, function):
        self.display_arrows = True
        self.buttons["forwardButton"] = function

    def registerBackwardButton(self, function):
        self.display_arrows = True
        self.buttons["backwardButton"] = function
    
    def registerLeftButton(self, function):
        self.display_arrows = True
        self.buttons["leftButton"] = function

    def registerRightButton(self, function):
        self.display_arrows = True
        self.buttons["rightButton"] = function
    
    def registerStopButton(self, function):
        self.display_arrows = True
        self.buttons["stopButton"] = function

    def _handleUserFunctionRequest(self, text) -> bool:
        print(f"Running {text}")
        try:
            user_function = self.buttons[text]
            if user_function is None:
                print("User function "+text+" not found")
                return False
            user_function()
            return True
        except:
            print("User function "+text+" caused an exception")
            return False

    def _generateHTML(self):

        string = _HTML1
        
        if self.display_arrows:
            string += _HTML_ARROWS

        string += f'<h3>Custom Function Bindings:</h3>'
        # add each button's href to html
        for button in self.buttons.keys():
            if(["forwardButton","backwardButton","leftButton","rightButton","stopButton"].count(button) > 0):
                # Slightly cursed solution to not display the arrow buttons as text buttons
                continue
            string += f'<p><a href=\"{button}"> <span><font size="30px">{button}</font></span></a></p>'
            string += "\n"

        string += f'<h3>Logged Data:</h3>'
        # add logged data to the html
        for data_label in self.logged_data.keys():
            string += f'<p>{data_label}: {str(self.logged_data[data_label])}</p>'
            string += "\n"

        string += _HTML2

        return string

""" Use decorators to bind the wifi methods to the requests """
wifi = Wifi()

@server.route("/", methods=['GET','POST'])
def index(request):
    return wifi.index_page(request)

@server.route("/wrong-host-redirect", methods=['GET'])
def wrong_host_redirect(request):
    return wifi.wrong_host_redirect(request)

@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    return wifi.hotspot(request)

@server.catchall()
def catch_all(request):
    return wifi.catch_all(request)

_HTML1 = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">

            <style>
                a { text-decoration: none; }

                html {
                    font-family: Arial;
                    display: inline-block;
                    margin: 0px auto;
                    text-align: center;
                }

            </style>
        </head>

        <body>
            <h2>XRP control page</h2>

            <p>
"""

_HTML_ARROWS = """
        <form action="forwardButton" method="post"><input type="submit" name="forwardButton"><span><font size="30px">&#8593;</font></span></input></form>
        <p></p>
        <button type=submit formmethod=POST formurl=\"/" name=\"leftButton"><span><font size="30px">&#8592;</font></span></button>
        &nbsp;&nbsp;
        <button type=submit formmethod=POST formurl=\"/" name=\"stopButton"><span><font size="30px">&#9744;</font></span></button>
        &nbsp;&nbsp;
        <button type=submit formmethod=POST formurl=\"/" name=\"rightButton"><span><font size="30px">&#8594;</font></span></button>
        <p></p>
        <button type=submit formmethod=POST formurl=\"/" name=\"backButton"><span><font size="30px">&#8595;</font></span></button>
"""

_HTML2 = """
            </p>

        </body>

        </html>
"""

from XRPLib.led import *

led = LED()
wifi.registerForwardButton(lambda: led.blink(2))
wifi.registerBackwardButton(lambda: led.blink(4))
wifi.registerLeftButton(lambda: led.on())
wifi.registerRightButton(lambda: led.off())
wifi.registerStopButton(lambda: led.change_state())
wifi.add_button("test", lambda: logging.debug("test"))
wifi.add_button("stopLED", lambda: led.off())
wifi.log_data("test", "test")
wifi.log_data("Int", 123)
wifi.log_data("Float", 123.456)
wifi.log_data("Bool", True)
wifi.log_data("None", None)
wifi.log_data("List", [1,2,3])
wifi.log_data("Dict", {"a":1,"b":2,"c":3})
wifi.log_data("Tuple", (1,2,3))
wifi.start_server(1)