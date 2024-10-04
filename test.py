from XRPLib.telemetry_sender import *

x = float_to_ascii(1234.56)

# print as list of bytes
print(list(x))

print(x)

print(ascii_to_float(x))