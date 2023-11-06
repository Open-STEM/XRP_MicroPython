from phew import server, template, logging, access_point, dns
from phew.template import render_template
from phew.server import redirect, stop, close
import gc
import network
import time
import json

logging.log_file = "webserverLog.txt"

class Webserver:

    @classmethod
    def get_default_webserver(cls):
        """
        Get the default webserver instance. This is a singleton, so only one instance of the webserver will ever exist.
        """
        return webserver

    def __init__(self):
        """
        Host a webserver for the XRP v2 Robot; Register your own callbacks and log your own data to the webserver using the methods below.
        """

        gc.threshold(50000) # garbage collection
        self.logged_data = {}
        self.buttons = {"forwardButton":    lambda: logging.debug("Button not initialized"),
                        "backButton":   lambda: logging.debug("Button not initialized"),
                        "leftButton":       lambda: logging.debug("Button not initialized"),
                        "rightButton":      lambda: logging.debug("Button not initialized"),
                        "stopButton":       lambda: logging.debug("Button not initialized")}
        self.FUNCTION_PREFIX = "startfunction"
        self.FUNCTION_SUFFIX = "endfunction"
        self.display_arrows = False
        # Instantiate self.wlan now so that running stop before start doesn't cause an error
        self.wlan = network.WLAN(network.STA_IF)

    def start_network(self, ssid:str=None, robot_id:int= None, password:str=None):
        """
        Open an access point from the XRP board to be used as a captive host. The default network information can be set in secrets.json

        :param ssid: The ssid of the access point, defaults to value from secrets.json
        :type ssid: str, optional
        :param robot_id: Replaces "{robot_id}" in ssid, defaults to value from secrets.json
        :type robot_id: int, optional
        :param password: The password of the access point, defaults to value from secrets.json
        :type password: str, optional
        """
        if ssid is None:
            try:
                with open("../../secrets.json") as secrets_file:
                    secrets = json.load(secrets_file)
                    ssid = str(secrets["ap_ssid"])
                    password = str(secrets["ap_password"])
                    if robot_id is None:
                        robot_id = str(secrets["robot_id"])
                ssid = ssid.replace("{robot_id}", robot_id)
            except (OSError, KeyError, ValueError):
                if robot_id is None:
                    robot_id = 1
                ssid = f"XRP_{robot_id}"
                password = "remote.xrp"
        if password is not None and len(password) < 8:
            logging.warn("Password is less than 8 characters, this may cause issues with some devices")
        self.wlan = access_point(ssid, password)
        logging.info(f"Starting Access Point \"{ssid}\"")
        self.ip = self.wlan.ifconfig()[0]

    def connect_to_network(self, ssid:str=None, password:str=None, timeout = 10):
        """
        Connect to a wifi network with the given ssid and password. 
        If the connection fails, the board will disconnect from the network and return.

        :param ssid: The ssid of the network, defaults to value from secrets.json
        :type ssid: str, optional
        :param password: The password of the network, defaults to value from secrets.json
        :type password: str, optional
        :param timeout: The amount of time to wait for the connection to succeed, defaults to 10
        :type timeout: int, optional
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True) # configure board to connect to wifi
        if ssid is None:
            try:
                with open("../../secrets.json") as secrets_file:
                    secrets = json.load(secrets_file)
                    ssid = str(secrets["wifi_ssid"])
                    password = str(secrets["wifi_password"])
            except (OSError, KeyError, ValueError):
                print("secrets.json not found or improperly formatted")
                return False
        self.wlan.connect(ssid,password)
        start_time = time.time()
        while not self.wlan.isconnected():
            print("Connecting to network, may take a second")
            if time.time() > start_time+timeout:
                print("Failed to connect to network, please try again")
                self.wlan.disconnect()
                return False
            time.sleep(0.25)
        self.ip = self.wlan.ifconfig()[0]

    def start_server(self):
        """
        Begin the webserver in either access point or bridge mode. The IP is printed to the console.

        Preconditions: Either start_network or connect_to_network must be called before this method.
        """
        self.wlan.active(True)
        logging.info(f"Starting DNS Server at {self.ip}")
        dns.run_catchall(self.ip)
        self.DOMAIN = self.ip
        logging.disable_logging_types(logging.LOG_INFO)
        server.run()

    def stop_server(self):
        """
        Shuts off the webserver and network and stops handling requests
        """
        if self.wlan.active():
            logging.enable_logging_types(logging.LOG_INFO)
            logging.info("Stopping Webserver and Network Connections")
            
            stop()
            self.wlan.active(False)

    def _index_page(self, request):
        # Render index page and respond to form requests
        if request.method == 'GET':
            return self._generateHTML()
        if request.method == 'POST':
            if str(list(request.form.values())[0]).count(" ") == 0:
                text = str(list(request.form.keys())[0])
            else:
                text = str(list(request.form.values())[0])
            self._handleUserFunctionRequest(text)
            return self._generateHTML()

    def _hotspot(self, request):
        # Redirect to Index Page
        return self._generateHTML()

    def _catch_all(self, request):
        # Catch all requests and redirect if necessary
        if request.headers.get("host") != self.DOMAIN:
            return redirect("http://"+self.DOMAIN+"/")
        return self._index_page(request=request)
        
    def log_data(self, label:str, data):
        """
        Register a custom label to be displayed on the webserver

        :param label: The label as it will be displayed, must be unique
        :type label: str
        :param data: The data to be displayed
        :type data: Any (converted to string)
        """
        self.logged_data[label] = data

    def add_button(self, button_name:str, function):
        """
        Register a custom button to be displayed on the webserver

        :param button_name: The label for the button as it will be displayed, must be unique
        :type button_name: str
        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.buttons[button_name] = function

    def registerForwardButton(self, function):
        """
        Assign a function to the forward button

        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.display_arrows = True
        self.buttons["forwardButton"] = function

    def registerBackwardButton(self, function):
        """
        Assign a function to the backward button

        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.display_arrows = True
        self.buttons["backButton"] = function
    
    def registerLeftButton(self, function):
        """
        Assign a function to the left button

        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.display_arrows = True
        self.buttons["leftButton"] = function

    def registerRightButton(self, function):
        """
        Assign a function to the right button

        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.display_arrows = True
        self.buttons["rightButton"] = function
    
    def registerStopButton(self, function):
        """
        Assign a function to the stop 
        
        :param function: The function to be called when the button is pressed
        :type function: function
        """
        self.display_arrows = True
        self.buttons["stopButton"] = function

    def _handleUserFunctionRequest(self, text) -> bool:
        print(f"Running {text}")
        try:
            user_function = self.buttons[text]
            if user_function is None:
                logging.warning("User function "+text+" not found")
                return False
            user_function()
            return True
        except RuntimeError as xcpt:
            logging.error("User function "+text+" caused an exception: "+str(xcpt))
            return False

    def _generateHTML(self):

        string = _HTML1
        
        if self.display_arrows:
            string += _HTML_ARROWS

        string += f'<h3>Custom Function Bindings:</h3>'
        # add each button's href to html
        for button in self.buttons.keys():
            if(["forwardButton","backButton","leftButton","rightButton","stopButton"].count(button) > 0):
                # Slightly cursed solution to not display the arrow buttons as text buttons
                continue
            string += f'<p><form action="{button}" method="post"><input type="submit" class="user-button" name={button} value="{button}" /></form></p>'
            string += "\n"

        string += f'<h3>Logged Data:</h3>'
        # add logged data to the html
        for data_label in self.logged_data.keys():
            string += f'<p>{data_label}: {str(self.logged_data[data_label])}</p>'
            string += "\n"

        string += _HTML2

        return string

""" Use decorators to bind the wifi methods to the requests """
webserver = Webserver()

@server.route("/", methods=['GET','POST'])
def index(request):
    return webserver._index_page(request)

@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    return webserver._hotspot(request)

@server.catchall()
def catch_all(request):
    return webserver._catch_all(request)

_HTML1 = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="refresh" content="1">
            
            <style>
                a { text-decoration: none; }

                html {
                    font-family: Arial;
                    display: inline-block;
                    margin: 0px auto;
                    text-align: center;
                }

                .arrow-button {
                    font-size: 30px;
                }

                .user-button {
                    font-size: 20px;
                }
            </style>
            
        </head>

        <body>
            <h2>XRP control page</h2>

            <p>
"""

_HTML_ARROWS = """
        <form action="forwardButton" method="post"><input type="submit" class="arrow-button" name="forwardButton" value=&#8593; /></form>
        <div style="display: flex; justify-content: center;">
        <form action="leftButton" method="post"><input type="submit" class="arrow-button" name="leftButton" value=&#8592; /></form>
        &nbsp;&nbsp;
        <form action="stopButton" method="post"><input type="submit" class="arrow-button" name="stopButton" value=&#9744; /></form>
        &nbsp;&nbsp;
        <form action="rightButton" method="post"><input type="submit" class="arrow-button" name="rightButton" value=&#8594; /></form>
        </div>
        <form action="backButton" method="post"><input type="submit" class="arrow-button" name="backButton" value=&#8595; /></form>
"""

_HTML2 = """
            </p>

        </body>

        </html>
"""