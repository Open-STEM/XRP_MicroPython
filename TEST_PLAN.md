# XRP MicroPython Library — Test Plan

## Overview

This test plan has two tiers:

1. **Unit tests** — Run on a desktop (CPython + pytest) with mocked hardware. These test pure logic: PID math, timeout behavior, arcade drive scaling, encoder math, data conversions, etc. They run in seconds and should be part of every PR/commit check.

2. **Hardware integration tests** — Run on an actual XRP robot (MicroPython). These verify that real hardware behaves correctly: motors spin, sensors read, timers fire, etc. They require a robot on a flat surface with batteries connected.

---

## Directory Structure

```
tests/
├── mocks/
│   ├── __init__.py
│   ├── machine.py          # Mock machine module (Pin, ADC, PWM, Timer, I2C)
│   ├── micropython.py      # Mock micropython module (const)
│   ├── rp2.py              # Mock rp2 module (PIO, StateMachine)
│   ├── neopixel.py         # Mock NeoPixel
│   └── sys_impl.py         # Mock sys.implementation
├── unit/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and mock installation
│   ├── test_pid.py          # PID controller logic
│   ├── test_timeout.py      # Timeout class
│   ├── test_motor.py        # Motor effort clamping and direction
│   ├── test_encoded_motor.py # EncodedMotor singleton and error handling
│   ├── test_encoder.py      # Encoder math (resolution, position conversion)
│   ├── test_differential_drive.py  # Arcade drive scaling, encoder-to-cm math
│   ├── test_imu_math.py     # IMU data conversions (_int16, _raw_to_mg, etc.)
│   ├── test_reflectance.py  # Reflectance normalization
│   ├── test_servo.py        # Servo angle-to-duty conversion
│   ├── test_motor_group.py  # MotorGroup aggregation logic
│   ├── test_board.py        # Board button logic, power detection
│   ├── test_rangefinder.py  # Rangefinder distance calculation
│   ├── test_webserver.py    # HTML generation, button registration
│   └── test_gamepad.py      # Gamepad data parsing
├── hardware/
│   ├── test_hw_motors.py        # Motor direction, speed, braking
│   ├── test_hw_encoders.py      # Encoder counting accuracy
│   ├── test_hw_drivetrain.py    # Straight/turn accuracy
│   ├── test_hw_rangefinder.py   # Distance measurement accuracy
│   ├── test_hw_reflectance.py   # Reflectance sensor readings
│   ├── test_hw_imu.py          # IMU readings and calibration
│   ├── test_hw_servo.py        # Servo movement
│   ├── test_hw_board.py        # LED, button, power switch
│   └── test_hw_timing.py       # Timer callback timing accuracy
└── README.md
```

---

## Tier 1: Unit Tests (Desktop, no hardware)

### How to run

```bash
cd XRP_MicroPython
pip install pytest
pytest tests/unit/ -v
```

### What is tested

| Test file | What it covers |
|-----------|---------------|
| `test_pid.py` | Proportional/integral/derivative math, output clamping, min_output behavior, integral windup, rate limiting, tolerance/is_done, clear_history |
| `test_timeout.py` | Timeout expiration, None timeout (never expires), ticks_diff correctness |
| `test_motor.py` | SinglePWMMotor effort clamping [0,1], direction flipping, DualPWMMotor direction XOR, brake/coast behavior, effort > 1.0 handling |
| `test_encoded_motor.py` | Invalid index raises exception (current bug), singleton pattern, speed-to-counts conversion, position inversion for flipped motors |
| `test_encoder.py` | Resolution calculation (585), position-to-revolutions conversion, wraparound handling (2^31/2^32) |
| `test_differential_drive.py` | Arcade drive scaling math, encoder-position-to-cm conversion, heading correction signs, straight/turn effort application |
| `test_imu_math.py` | `_int16` conversion, `_raw_to_mg`/`_raw_to_mdps` scaling, scale factor updates, angle integration math |
| `test_reflectance.py` | ADC normalization to [0, 1], edge values (0, 65535) |
| `test_servo.py` | Angle-to-duty_ns conversion, boundary angles (0, 200), free() behavior |
| `test_motor_group.py` | Average position/speed across motors, add/remove, set_effort delegation |
| `test_board.py` | `are_motors_powered` threshold, `is_button_pressed` inversion |
| `test_rangefinder.py` | Pulse-width-to-cm conversion, timeout handling (MAX_VALUE), instance registration |
| `test_webserver.py` | HTML generation, button registration, arrow display toggle |
| `test_gamepad.py` | Packet parsing, value normalization, button press detection |

---

## Tier 2: Hardware Integration Tests (On-device)

### Prerequisites

- XRP robot with batteries connected and power switch ON
- Robot placed on a flat, open surface (at least 50cm x 50cm clear space)
- Ultrasonic rangefinder pointed at a wall or flat surface at a known distance
- USB connection to upload and run tests
- A ruler/tape measure for distance verification

### How to run

Upload the desired test file to the robot and run it. Each test prints PASS/FAIL results to the REPL console.

```
# Upload via your preferred tool (Thonny, mpremote, etc.)
mpremote run tests/hardware/test_hw_motors.py
```

### Test procedures

#### `test_hw_motors.py` — Motor Direction and Speed
**Setup:** Robot wheels elevated (not touching ground), or accept it will move.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Forward effort | `set_effort(0.5)` on both motors | Both wheels spin forward |
| Reverse effort | `set_effort(-0.5)` on both motors | Both wheels spin backward |
| Left/right independence | Left forward, right reverse | Wheels spin opposite directions |
| Brake | `set_effort(0.5)` then `brake()` | Motor resists turning by hand |
| Coast | `set_effort(0.5)` then `coast()` | Motor spins freely |
| Zero effort | `set_effort(0)` | Motor stops |
| Effort clamping | `set_effort(1.5)` | No crash; treated as 1.0 |
| Speed control | `set_speed(60)`, wait 2s, read `get_speed()` | Speed within 10% of 60 RPM |

#### `test_hw_encoders.py` — Encoder Counting
**Setup:** Robot wheels elevated.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Count direction | Spin wheel forward by hand, read counts | Counts increase |
| Reverse counts | Spin wheel backward by hand, read counts | Counts decrease |
| Reset | Reset encoder, read position | Position is 0 |
| Resolution | Drive motor exactly 1 revolution at low speed | ~585 counts |
| Consistency | Read position 100 times rapidly | All reads return same value (wheel stationary) |

#### `test_hw_drivetrain.py` — Drivetrain Accuracy
**Setup:** Robot on flat surface, mark starting position.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Straight 30cm | `drivetrain.straight(30)` | Robot travels 28-32cm (measure with ruler) |
| Straight -30cm | `drivetrain.straight(-30)` | Robot returns close to start |
| Turn 90 CW | `drivetrain.turn(90)` | Robot turns ~90 degrees (visual check) |
| Turn 90 CCW | `drivetrain.turn(-90)` | Robot turns back |
| Square | 4x `straight(20)` + `turn(90)` | Robot ends near starting position |
| Timeout | `drivetrain.straight(1000, timeout=2)` | Returns False within ~2 seconds |
| Returns True | `drivetrain.straight(10)` | Returns True |

#### `test_hw_rangefinder.py` — Distance Measurement
**Setup:** Place a flat surface (wall/book) at a known distance from the sensor.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Known distance | Place wall at 20cm, read `distance()` | Reads 18-22cm |
| Min range | Place wall at 3cm | Reads 2-5cm |
| Max range | Point at open space (>4m) | Returns MAX_VALUE (65535) |
| Stability | Take 10 readings at fixed distance | Standard deviation < 1cm |
| Non-blocking | Call `distance()` 100 times, measure total time | < 200ms total (non-blocking) |
| First read blocks | Create new Rangefinder, time first `distance()` | Blocks briefly, then returns valid reading |

#### `test_hw_reflectance.py` — Reflectance Sensors
**Setup:** White paper and dark surface available.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| White surface | Place sensor over white paper | Both read < 0.3 |
| Dark surface | Place sensor over dark surface | Both read > 0.7 |
| Left/right independent | Cover only left sensor | Left changes, right stays |

#### `test_hw_imu.py` — IMU Readings
**Setup:** Robot on flat, stable surface. Do not move during calibration tests.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Connection | `imu.is_connected()` | Returns True |
| Gravity | Read accelerometer Z-axis | ~1000 mg (within 100) |
| Gravity X/Y | Read accelerometer X/Y | Near 0 (within 100 mg) |
| Gyro at rest | Read gyroscope at rest | All axes near 0 (within 50 mdps) after calibration |
| Yaw integration | Manually rotate 90 degrees, read `get_yaw()` | ~90 degrees (within 10) |
| Calibration | Run `calibrate()`, check offsets | Offsets are non-zero; subsequent readings are near zero at rest |
| Temperature | Read `temperature()` | 15-45 C (reasonable room temp) |

#### `test_hw_servo.py` — Servo Movement
**Setup:** Servo attached with visible arm/horn.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Set 0 | `set_angle(0)` | Servo moves to one extreme |
| Set 90 | `set_angle(90)` | Servo moves to middle |
| Set 180 | `set_angle(180)` | Servo moves to other extreme |
| Free | `free()` | Servo can be moved by hand freely |

#### `test_hw_board.py` — Board Peripherals
**Setup:** None special.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| LED on/off | `led_on()` then `led_off()` | LED turns on then off (visual) |
| LED blink | `led_blink(5)` | LED blinks ~5 Hz (visual) |
| Button | Press and release button, read `is_button_pressed()` | Returns True when pressed, False when released |
| Power detect | With batteries connected: `are_motors_powered()` | Returns True |
| Power detect off | With batteries disconnected | Returns False |
| RGB LED | `set_rgb_led(255, 0, 0)` then `(0, 255, 0)` then `(0, 0, 255)` | LED changes to red, green, blue (newer boards only) |

#### `test_hw_timing.py` — Timer Callback Accuracy
**Setup:** None special.

| Test | Procedure | Pass criteria |
|------|-----------|---------------|
| Motor update rate | Count motor `_update` calls over 1 second | 45-55 calls (target: 50 Hz) |
| IMU update rate | Count IMU `_update_imu_readings` calls over 1 second | 190-220 calls (target: 208 Hz) |
| Rangefinder period | Measure time between rangefinder pings | 55-65ms per ping |
| Callback interference | Run all timers simultaneously for 10s | No crashes, no watchdog resets |

---

## Regression Checklist

When making changes, run:

1. All unit tests (`pytest tests/unit/ -v`)
2. If motor/encoder changes: `test_hw_motors.py`, `test_hw_encoders.py`
3. If drivetrain/PID changes: `test_hw_drivetrain.py`
4. If sensor changes: relevant `test_hw_*.py`
5. If timer/IRQ changes: `test_hw_timing.py`
6. Full hardware suite before any release

---

## Known Limitations

- Unit tests mock all hardware; they cannot catch real timing issues, I2C failures, or PIO state machine bugs
- Hardware tests require human observation for some checks (LED visual, servo movement)
- Drivetrain accuracy tests are approximate due to surface friction variations
- IMU yaw integration tests require manual rotation and are inherently imprecise
- No automated CI pipeline is possible for hardware tests
