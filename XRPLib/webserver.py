import machine
import utime
import network
import socket
import _thread
import time

SSID = "XRPbot1"
PASSWORD = '12345678'

class Button:
    def __init__(self, function):
        self.callback = function
        self.name = function.__name__

class WebServer:

    def __init__(self):

        self.buttons = []

        # prefix for each button's href
        self.FUNCTION_PREFIX = "startfunction"
        self.FUNCTION_SUFFIX = "endfunction"

        self.forwardCallback = lambda: print("no forward function registered")
        self.leftCallback = lambda: print("no left function registered")
        self.rightCallback = lambda: print("no right function registered")
        self.backCallback = lambda: print("no back function registered")
        self.stopCallback = lambda: print("no stop function registered")

        # function to run when a button is pressed
        self.functionToRun = None
        self.lock = _thread.allocate_lock()

        # we want to ignore the first request (when page is loaded, it sends a request automatically)
        self.isFirstRequest = True

    def addButton(self, function):
        self.buttons.append(Button(function))

    def registerForwardButton(self, function):
        self.forwardCallback = function

    def registerLeftButton(self, function):
        self.leftCallback = function

    def registerRightButton(self, function):
        self.rightCallback = function

    def registerBackButton(self, function):
        self.backCallback = function

    def registerStopButton(self, function):
        self.stopCallback = function

    def run(self):

        # start a new thread for the IO
        #_thread.start_new_thread(self._runUserThread, ())
        self._runIOThread()

    


    # run on a separate thread to handle IO
    def _runIOThread(self):

        print("run IO thread")

        self.wlan, self.socket = self._initServer()

        # Listen for connections
        while True:
            try:
                cl, addr = self.socket.accept()
                print('client connected from', addr)
                request = cl.recv(1024)

                result = self._handleRequest(str(request))

                if not result:
                    print("no function found")
                print("before function to run")
                    
                if self.functionToRun is not None:
                    self.functionToRun()
                    self.functionToRun = None
                print("after functio nto run")

                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(self._generateHTML())
                cl.close()
                print("succesfully sent html")
            
            except OSError as e:
                print('connection closed')
                cl.close()
            

       # self.wlan.active(False)

    # called on the webserver thread.
    def _setFunctionToRun(self, function):
        self.functionToRun = function

    # returns wlan, socket
    def _initServer(self):

        wlan = network.WLAN(network.AP_IF)
        wlan.active(False)
        wlan.config(essid=SSID, password=PASSWORD)
        wlan.active(True)

        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            utime.sleep(1)

        if wlan.status() != 3:
            print (wlan.status())
            raise RuntimeError('network connection failed')
        else:
            print('connected')
            status = wlan.ifconfig()
            print( 'ip = ' + status[0] )

        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

        s = socket.socket()
        s.bind(addr)
        s.listen(1)

        print('listening on', addr)

        return wlan, s

    # returns the string after the substring, or None if not found
    def _getStringAfter(self, fullString, substring):
        index = fullString.find(substring)
        if index == -1:
            return None
        else:
            rest_of_string = fullString[index + len(substring):]
            return rest_of_string

    def _getStringBefore(self, fullString, substring):
        index = fullString.find(substring)
        if index == -1:
            return None
        else:
            string_before_substring = fullString[:index]
            return string_before_substring

    def _getCallbackByFunctionName(self, functionName):
        for button in self.buttons:
            if button.name == functionName:
                return button.callback
        return None
    

    def _indexOfSubstring(self, list, substring):
        for i in range(len(list)):
            if substring in list[i]:
                return i
        return -1
    
    def _handleUserFunctionRequest(self, request):
        stringWithSuffix = self._getStringAfter(request, self.FUNCTION_PREFIX)

        if stringWithSuffix is None:
            return False

        functionName = self._getStringBefore(stringWithSuffix, self.FUNCTION_SUFFIX)

        if functionName is None:
            return False

        functionCallback = self._getCallbackByFunctionName(functionName)

        if functionCallback is None:
            return False
        
        # matching function callback. Call it and successful return
        self._setFunctionToRun(functionCallback)
        return True

    def _handleRequest(self, fullRequest):

        request = fullRequest.split(" ")
        print(request)
        index = self._indexOfSubstring(request[:-1], "GET")
        if index == -1:
            return False
        request = request[index + 1]
        print("Filtered request:", request)

        userFunctionRequestSuccess = self._handleUserFunctionRequest(fullRequest)

        # if userFunctionRequestSuccess, then we don't need to check for arrow buttons
        if userFunctionRequestSuccess:
            return True

        if "forwardbutton" in fullRequest:
            self._setFunctionToRun(self.forwardCallback)
        elif "leftbutton" in fullRequest:
            self._setFunctionToRun(self.leftCallback)
        elif "rightbutton" in fullRequest:
            self._setFunctionToRun(self.rightCallback)
        elif "backbutton" in fullRequest:
            self._setFunctionToRun(self.backCallback)
        elif "stopbutton" in fullRequest:
            self._setFunctionToRun(self.stopCallback)
        else:
            print("no function found")
            return False

        return True

    def _generateHTML(self):

        string = _HTML1 + _HTML_ARROWS

        # add each button's href to html
        for button in self.buttons:
            buttonID = self.FUNCTION_PREFIX + button.name + self.FUNCTION_SUFFIX
            string += f'<p><a href=\"{buttonID}"> <span><font size="30px">{button.name}</font></span></a></p>'
            string += "\n"

        string += _HTML2

        return string

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
        <a href=\"forwardbutton"> <span><font size="30px">&#8593;</font></span></a>
        <p></p>
        <a href=\"leftbutton"> <span><font size="30px">&#8592;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"stopbutton"> <span><font size="30px">&#9744;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"rightbutton"> <span><font size="30px">&#8594;</font></span></a>
        <p></p>
        <a href=\"backbutton"> <span><font size="30px">&#8595;</font></span></a>
"""

_HTML2 = """
            </p>

        </body>

        </html>
"""

