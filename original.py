import machine
import utime
import network
import socket

selection = 0

def blink(selection):
    times = selection
    while times > 0:
        print("LED ON")
        utime.sleep(0.5)
        print("LED OFF")
        utime.sleep(0.5)
        times = times - 1

def square():
    print("Making a square")

def keepaway():
    print("Keep away")

def imufun():
    print("IMU Fun")

def webpage():
    html = """
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
        <a href=\"foward"> <span><font size="30px">&#8593;</font></span></a>
        <p></p>
        <a href=\"left"> <span><font size="30px">&#8592;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"stop"> <span><font size="30px">&#9744;</font></span></a>
        &nbsp;&nbsp;
        <a href=\"right"> <span><font size="30px">&#8594;</font></span></a>
        <p></p>
        <a href=\"backward"> <span><font size="30px">&#8595;</font></span></a>
    <p></p><p></p><p></p>
    <p><a href=\"square"> <span><font size="30px">square</font></span></a></p>
    <p><a href=\"keepaway"> <span><font size="30px">keepaway</font></span></a></p>
    <p><a href=\"imufun"> <span><font size="30px">imufun</font></span></a></p>
    <p><a href=\"stopServing"> <span><font size="30px">turn of WiFi</font></span></a></p>
    </p>

</body>

</html>
    """
    return html

def startweb():
    ssid = "XRPbot1"
    password = '12345678'

    wlan = network.WLAN(network.AP_IF)
    wlan.active(False)
    wlan.config(essid=ssid, password=password)
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

    # Listen for connections
    while True:
        try:
            cl, addr = s.accept()
            print('client connected from', addr)
            request = cl.recv(1024)
            print(request)

            request = str(request)

            if request.find("/foward") == 6:
                print("forward")
            elif request.find("/left") == 6:
                print("left")
            elif request.find("/right") == 6:
                print("right")
            elif request.find("/backward") == 6:
                print("backward")
            elif request.find("/stop") == 6:
                print("Stop")
            elif request.find("/square") == 6:
                square()
            elif request.find("/keepaway") == 6:
                keepaway()
            elif request.find("/imufun") == 6:
                imufun()
            elif request.find("/stopServing") == 6:
                break

            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.send(webpage())
            cl.close()

        except OSError as e:
            cl.close()
            print('connection closed')
    wlan.active(False)


while True:
    startweb()


