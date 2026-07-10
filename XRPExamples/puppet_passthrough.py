from XRPLib.board import Board
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.servo import Servo
from XRPLib.puppet import (Puppet, VAR_TYPE_INT, VAR_TYPE_FLOAT, VAR_TYPE_BOOL,
                           PERM_READ_ONLY, PERM_WRITE_ONLY)
from machine import Pin
import sys
import time

# Puppet passthrough: hand direct control of the robot's actuators to the
# XRPWeb dashboard.
#
# The dashboard starts this program the same way the Run button starts any
# program, then streams XPP variable updates into the write-only variables
# defined below. Defining a custom variable sends its definition to the
# browser, which is how the dashboard learns that the passthrough is running
# and which actuator channels this board actually has. Stop it from XRPWeb
# like any other program; the puppet protocol deliberately lets the interrupt
# through even while it owns the USB stream.

# Motors stop when the link goes quiet for this long (browser sends a
# keepalive twice a second while the dashboard controls are open).
WATCHDOG_TIMEOUT_MS = 2000

# Collect the actuators this board has. The get_default_* helpers return an
# Exception object (they do not raise) for ports the board lacks, e.g. servo
# 3/4 and motor 4 on some boards, so missing channels are never defined and
# never shown in the browser.
servos = {}
for index in range(1, 5):
    servo = Servo.get_default_servo(index=index)
    if not isinstance(servo, Exception):
        servos['$servo.' + str(index)] = servo

motors = {}
for name, index in (('$motor.left', 1), ('$motor.right', 2),
                    ('$motor.3', 3), ('$motor.4', 4)):
    motor = EncodedMotor.get_default_encoded_motor(index=index)
    if not isinstance(motor, Exception):
        motors[name] = motor

board = Board.get_default_board()
drivetrain = DifferentialDrive.get_default_differential_drive()

puppet = Puppet.get_default_puppet()
for name in servos:
    puppet.define_variable(name, VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
for name in motors:
    puppet.define_variable(name, VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
puppet.define_variable('$led', VAR_TYPE_BOOL, PERM_WRITE_ONLY)
# Browser liveness ticker; only its arrival matters, never its value.
puppet.define_variable('$puppet.keepalive', VAR_TYPE_INT, PERM_WRITE_ONLY)
# Drivetrain motion commands, browser -> robot: a nonzero value starts a
# BLOCKING drivetrain call ($drivetrain.straight is a distance in cm,
# negative = backward; $drivetrain.turn is degrees, positive =
# counterclockwise). While one runs, this program's main loop is stopped:
# incoming packets still land in the registry (parsing happens in interrupt
# context), but sliders, the LED, button events and the watchdog all wait.
# $drivetrain.busy is the browser's only feedback during the motion.
#
# The .effort variables are parameters, not commands: the browser writes
# them before the trigger (writes apply in order), they carry the max_effort
# for the next motion, and they persist across motions like a setting.
puppet.define_variable('$drivetrain.straight', VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
puppet.define_variable('$drivetrain.straight.effort', VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
puppet.define_variable('$drivetrain.turn', VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
puppet.define_variable('$drivetrain.turn.effort', VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
puppet.define_variable('$drivetrain.busy', VAR_TYPE_BOOL, PERM_READ_ONLY)


def _drive_effort(name):
    """Sanitize a drive effort parameter: an unwritten (0.0) or out-of-range
    value falls back to XRPLib's 0.5 default - a blocking call at effort 0
    would just sit there until its timeout."""
    effort = puppet.get_variable(name)
    if not 0.0 < effort <= 1.0:
        effort = 0.5
    return effort

# User button state, robot -> browser.
puppet.define_variable('$button', VAR_TYPE_BOOL, PERM_READ_ONLY)

# Board type, robot -> browser: 0 = Beta XRP, 1 = XRP, 2 = NanoXRP.
# XPP has no string type, so the browser maps the code back to a name. The
# detection mirrors what the IDE keys off the version string: the machine
# name carries "NanoXRP" on the Cytron board and "RP2350" on the standard
# XRP; any other RP2040 build is the beta.
puppet.define_variable('$board.type', VAR_TYPE_INT, PERM_READ_ONLY)
machine_name = sys.implementation._machine
if 'NanoXRP' in machine_name:
    puppet.set_variable('$board.type', 2)
elif 'RP2350' in machine_name:
    puppet.set_variable('$board.type', 1)
else:
    puppet.set_variable('$board.type', 0)

# Report the user button by interrupt, not by polling: the edge IRQ only
# raises a flag (safe in any IRQ context - no allocation, no BLE/USB writes),
# and the main loop reads the pin and pushes the update. The 50 Hz loop
# coalesces contact bounce and the last-state check drops duplicates.
button_event = False

def _on_button_edge(pin):
    global button_event
    button_event = True

board.button.irq(_on_button_edge, Pin.IRQ_RISING | Pin.IRQ_FALLING)

# Send the initial state so the browser starts out correct.
last_button = board.is_button_pressed()
puppet.set_variable('$button', last_button)

# Apply commands as they change. Each actuator is left untouched until the
# dashboard writes its first value, so starting the passthrough never snaps
# the servos or spins the motors.
watched = list(servos.keys()) + list(motors.keys()) + ['$led']
last_applied = {name: puppet.get_variable(name) for name in watched}


def _run_drive_command(action):
    """Run a blocking drivetrain call with the bookkeeping both commands share.

    busy is pushed True first (the browser's only signal during the run) and
    False after. The finally also discards everything that arrived mid-motion:
    both command variables (commands while busy are ignored), and the motor
    efforts - the drivetrain call ends with the motors stopped, so the
    registry and last_applied are zeroed to match; without that, pre-drive
    slider values would be silently re-applied the moment the motion ends.
    The .effort parameter variables are deliberately left alone: they are
    settings, not actuator state.
    """
    puppet.set_variable('$drivetrain.busy', True)
    try:
        action()
    finally:
        puppet.set_variable('$drivetrain.straight', 0.0)
        puppet.set_variable('$drivetrain.turn', 0.0)
        for name in motors:
            puppet.set_variable(name, 0.0)
            last_applied[name] = 0.0
        puppet.set_variable('$drivetrain.busy', False)

# Watchdog state: any received packet counts as liveness (slider updates,
# LED toggles and the keepalive ticker all refresh it).
last_rx_count = puppet.packets_received
last_rx_ms = time.ticks_ms()

while True:
    now = time.ticks_ms()
    if puppet.packets_received != last_rx_count:
        last_rx_count = puppet.packets_received
        last_rx_ms = now

    for name, servo in servos.items():
        angle = puppet.get_variable(name)
        if angle != last_applied[name]:
            last_applied[name] = angle
            servo.set_angle(min(max(angle, 0.0), 180.0))

    for name, motor in motors.items():
        effort = puppet.get_variable(name)
        if effort != last_applied[name]:
            last_applied[name] = effort
            motor.set_effort(min(max(effort, -1.0), 1.0))

    led = puppet.get_variable('$led')
    if led != last_applied['$led']:
        last_applied['$led'] = led
        if led:
            board.led_on()
        else:
            board.led_off()

    # Button edge fired: read the pin once and push the new state.
    if button_event:
        button_event = False
        pressed = board.is_button_pressed()
        if pressed != last_button:
            last_button = pressed
            puppet.set_variable('$button', pressed)

    # Blocking drivetrain commands (see _run_drive_command for the shared
    # bookkeeping). A timeout always bounds the motion - otherwise a jammed
    # or lifted robot would freeze this loop (and the watchdog) forever -
    # and it scales with the commanded effort, since a slow drive
    # legitimately needs more time before it counts as stuck.
    distance = puppet.get_variable('$drivetrain.straight')
    if distance != 0.0:
        effort = _drive_effort('$drivetrain.straight.effort')
        _run_drive_command(
            lambda: drivetrain.straight(distance, max_effort=effort,
                                        timeout=abs(distance) / (10.0 * effort) + 3.0))

    degrees = puppet.get_variable('$drivetrain.turn')
    if degrees != 0.0:
        effort = _drive_effort('$drivetrain.turn.effort')
        _run_drive_command(
            lambda: drivetrain.turn(degrees, max_effort=effort,
                                    timeout=abs(degrees) / (90.0 * effort) + 3.0))

    # Safety: if the browser goes quiet (tab closed, cable pulled, BLE drop),
    # stop the motors rather than let the robot drive away on a stale effort.
    # Servos and the LED are harmless to leave as they are. The stale effort
    # is also cleared from the puppet registry so a reconnecting browser
    # can't resurrect it — driving resumes only on a fresh slider command.
    if time.ticks_diff(now, last_rx_ms) > WATCHDOG_TIMEOUT_MS:
        for name, motor in motors.items():
            if last_applied[name] != 0.0:
                last_applied[name] = 0.0
                puppet.set_variable(name, 0.0)
                motor.set_effort(0.0)

    time.sleep(0.02)
