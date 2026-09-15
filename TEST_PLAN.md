# XRP MicroPython Library — Test Plan

## Overview

This test plan has three tiers:

1. **Unit tests** — Run on a desktop (CPython + pytest) with mocked hardware. These test pure logic: PID math, timeout behavior, arcade drive scaling, encoder math, data conversions, etc. They run in seconds and should be part of every PR/commit check.

2. **Hardware integration tests (manual)** — Run on an XRP board (MicroPython) with a human operator. The operator presses a button to start, places surfaces for reflectance tests, and visually verifies LEDs and servos.

3. **Hardware integration tests (automated test stand)** — The same tests run unattended on a dedicated test board. A `/teststand_mode` flag file on the Pico switches tests to auto-start and use instrumentation sensors instead of human verification. Triggered automatically on code checkins via GitHub Actions.

---

## Directory Structure

```
tests/
├── mocks/
│   ├── __init__.py
│   ├── machine.py          # Mock machine module (Pin, ADC, PWM, Timer, I2C)
│   ├── rp2.py              # Mock rp2 module (PIO, StateMachine)
│   └── neopixel.py         # Mock NeoPixel
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
│   ├── teststand.py             # Test stand detection and sensor helpers
│   ├── run_all_hw_tests.py      # Master runner (JSON output for CI)
│   ├── test_hw_motors.py        # Motor direction, speed, braking
│   ├── test_hw_encoders.py      # Encoder counting accuracy
│   ├── test_hw_drivetrain.py    # Straight/turn accuracy
│   ├── test_hw_rangefinder.py   # Distance measurement accuracy
│   ├── test_hw_reflectance.py   # Reflectance sensor readings
│   ├── test_hw_imu.py          # IMU readings and calibration
│   ├── test_hw_servo.py        # Servo movement
│   ├── test_hw_board.py        # LED, button, power switch
│   └── test_hw_timing.py       # Timer callback timing accuracy
scripts/
│   └── ci_hardware_test.py     # Host-side CI script (sync + run + parse)
.github/workflows/
│   └── hardware-test.yml       # GitHub Actions (unit + hardware tests)
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

## Tier 2: Hardware Integration Tests

### Two modes of operation

All hardware tests support two modes, controlled by the presence of a `/teststand_mode` file on the Pico's filesystem:

| | Manual Mode | Test Stand Mode |
|---|---|---|
| **Start** | Press user button | Starts immediately |
| **LED verification** | Visual check by human | Phototransistor reads ADC |
| **Servo verification** | Visual check by human | Break-beam sensor detects arm position |
| **Reflectance surfaces** | Human places white/dark paper | Servo-actuated sliding plate |
| **RGB LED** | Visual check by human | TCS34725 RGB color sensor (Phase 4) |
| **Button test** | Human presses button | GPIO toggle via spare pin (optional) |

### Manual mode

#### Prerequisites

- XRP board with batteries connected and power switch ON
- Motors plugged in, shafts free to spin
- Ultrasonic rangefinder pointed at a wall or flat surface at a known distance
- USB connection to upload and run tests
- White paper and dark surface available (for reflectance tests)

#### How to run

```bash
# Run a single test file
mpremote run tests/hardware/test_hw_motors.py

# Run all tests (will pause for button presses)
mpremote run tests/hardware/run_all_hw_tests.py
```

### Test stand mode (automated)

#### Prerequisites

- Automated test board with XRP controller PCB, motors, sensors mounted (see Test Stand Design below)
- `/teststand_mode` file on Pico filesystem: `mpremote exec "f = open('/teststand_mode', 'w'); f.close()"`
- USB connection to CI host

#### How to run

```bash
# Run all tests automatically (no button presses, no human checks)
mpremote run tests/hardware/run_all_hw_tests.py

# Or use the CI script which handles sync + run + parse
python scripts/ci_hardware_test.py
```

---

### Test procedures

#### `test_hw_motors.py` — Motor Direction and Speed
**Setup:** Motor shafts free to spin (no load).

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Forward effort | `set_effort(0.5)` on both motors for 1s | Both encoder positions > 0 | Encoder (auto) |
| Reverse effort | `set_effort(-0.5)` on both motors for 1s | Both encoder positions < 0 | Encoder (auto) |
| Independent direction | Left forward, right reverse for 1s | Left > 0, right < 0 | Encoder (auto) |
| Brake | `set_effort(0.5)` then `brake()` | Position stable (< 0.1 rev drift) | Encoder (auto) |
| Coast | `set_effort(0.5)` then `coast()` | No crash | Auto |
| Speed control | `set_speed(60)`, wait 2s | Speed 50-70 RPM | Encoder (auto) |
| Zero effort | `set_effort(0)` | Position stable | Encoder (auto) |

#### `test_hw_encoders.py` — Encoder Counting
**Setup:** Motor shafts free to spin.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Count direction | Drive motor forward 1s | Counts > 0 | Encoder (auto) |
| Reverse counts | Drive motor backward 1s | Counts < 0 | Encoder (auto) |
| Reset | Drive, reset, read | Position ≈ 0 | Encoder (auto) |
| Resolution | Drive ~1 revolution | 500-700 counts (~585 expected) | Encoder (auto) |
| Stationary consistency | 10 rapid reads, motor stopped | Spread ≤ 2 counts | Encoder (auto) |

#### `test_hw_drivetrain.py` — Drivetrain Accuracy
**Setup:** Motors free to spin. Manual mode: flat surface with clear space.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Straight 30cm | `straight(30, max_effort=0.5)` | Encoder avg 25-35cm | Encoder (auto) |
| Reverse 30cm | `straight(-30, max_effort=0.5)` | Encoder avg -35 to -25cm | Encoder (auto) |
| Turn 90 CW | `turn(90, max_effort=0.5)` | IMU yaw 80-100° | IMU (auto) |
| Turn 90 CCW | `turn(-90, max_effort=0.5)` | IMU yaw -100 to -80° | IMU (auto) |
| Timeout | `straight(10000, timeout=2)` | Returns False in < 3s | Timer (auto) |
| Square | 4× straight(20) + turn(90) | Final heading 340-380° | IMU (auto) |

#### `test_hw_rangefinder.py` — Distance Measurement
**Setup:** Flat surface at known distance. Test stand: fixed wall at ~20cm.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| First reading | `distance()` | Returns a number | Type check (auto) |
| Reasonable range | `distance()` | 2-400cm or MAX_VALUE | Range check (auto) |
| Stability | 10 readings, 100ms apart | Max deviation < 3cm | Variance (auto) |
| Non-blocking | 100 calls, measure time | < 200ms total | Timer (auto) |

#### `test_hw_reflectance.py` — Reflectance Sensors
**Manual:** Human places white/dark surfaces and presses button.
**Test stand:** Servo-actuated sliding plate with white/black halves.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Values in range | Read both sensors | 0 ≤ value ≤ 1 | Range check (auto) |
| White surface | Sensors over white | Both < 0.4 | ADC (auto) |
| Dark surface | Sensors over dark | Both > 0.6 | ADC (auto) |

#### `test_hw_imu.py` — IMU Readings
**Setup:** Board flat and stationary.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Connection | `is_connected()` | True | I2C (auto) |
| Gravity Z | Read accelerometer Z | 800-1200 mg | IMU (auto) |
| Gravity X/Y | Read accelerometer X, Y | |X|, |Y| < 200 mg | IMU (auto) |
| Gyro at rest | Read gyroscope | All axes < 100 mdps | IMU (auto) |
| Yaw drift | Reset yaw, wait 5s | Drift < 3° | IMU (auto) |
| Temperature | `temperature()` | 15-45°C | IMU (auto) |
| Batch read | `get_acc_gyro_rates()` | 2×3 array | Shape check (auto) |

#### `test_hw_servo.py` — Servo Movement
**Manual:** Visual check of servo arm.
**Test stand:** Break-beam sensor detects arm position at 0° vs 180°.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Angle sweep | Set 0°, 90°, 180°, 90° | No crash; arm moves | Manual: visual. Stand: break-beam state changes |
| Free | `set_angle(90)` then `free()` | Servo releases | Manual: move by hand. Stand: no-crash check |

#### `test_hw_board.py` — Board Peripherals
**Manual:** Visual check for LEDs, human button press.
**Test stand:** Phototransistor for LED, GPIO toggle for button.

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| LED on/off | `led_on()` / `led_off()` | LED changes state | Manual: visual. Stand: phototransistor ADC delta > 1000 |
| LED blink | `led_blink(5)` for 1s | ~5 Hz blink | Manual: visual. Stand: 6-14 ADC transitions |
| Button press | Press and release button | Detected correctly | Manual: human press. Stand: GPIO toggle |
| Power detect | Read `are_motors_powered()` | True (batteries connected) | ADC (auto) |
| RGB LED | Set red, green, blue | Colors display | Manual: visual. Stand: TCS34725 (Phase 4) |

#### `test_hw_timing.py` — Timer Callback Accuracy

| Test | Procedure | Pass criteria | Verification |
|------|-----------|---------------|-------------|
| Motor update rate | Count callbacks for 1s | 40-60 Hz (target: 50) | Callback counter (auto) |
| IMU update rate | Count callbacks for 1s | 150-260 Hz (target: 208) | Callback counter (auto) |
| All timers | Run all timers for 10s | No crash | Survival check (auto) |

---

## Tier 3: Automated Test Stand Design

### Physical Layout

The XRP controller PCB is mounted directly on a flat test board (~20cm × 25cm) with all peripherals. No chassis needed — the robot never drives anywhere.

```
┌──────────────────────────────────────────────┐
│  Test Board (~20cm x 25cm)                   │
│                                              │
│  ┌──────────────────┐                        │
│  │ XRP Controller   │ mounted flat           │
│  │ PCB (Pico W)     │ (has LED, NeoPixel,    │
│  │                  │  IMU, button on-board)  │
│  └──────────────────┘                        │
│                                              │
│  ┌────┐  ┌────┐                              │
│  │ M1 │  │ M2 │  motors bolted down,         │
│  └────┘  └────┘  shafts free (no wheels)     │
│                                              │
│  Rangefinder ─────► Fixed wall panel at 20cm │
│                                              │
│  ┌───────────┐                               │
│  │Reflectance│◄── sliding plate              │
│  │ sensors   │    (white/black halves)        │
│  └───────────┘    actuated by stand servo     │
│                                              │
│  Servo ──► break-beam sensor                 │
│                                              │
│  LED ◄── phototransistor in light tube       │
│  NeoPixel ◄── RGB color sensor (I2C)         │
└──────────────────────────────────────────────┘
```

### Instrumentation wiring (spare Motor 3/4 and Servo 3/4 ports)

| Connection | From | To | Purpose |
|---|---|---|---|
| LED sensor | Phototransistor (TEPT5700) | MOTOR_3_ENCODER_A (ADC) | Detect LED on/off/blink |
| Servo sensor | Break-beam phototransistor | MOTOR_3_ENCODER_B (digital in) | Detect servo arm position |
| Reflectance slide | Small servo | SERVO_4 (PWM) | Move white/black plate under sensors |
| RGB sensor | TCS34725 (I2C, addr 0x29) | I2C_SDA_1 / I2C_SCL_1 | Detect NeoPixel colors |
| Button test | SERVO_3 (GPIO output) | BOARD_USER_BUTTON via 1kΩ | Optional: toggle button pin |

### Build phases

| Phase | What | Tests enabled |
|---|---|---|
| **1: Software only** | `teststand.py`, `run_all_hw_tests.py`, `ci_hardware_test.py`, GitHub Actions workflow. Tests auto-start, visual checks skipped. | 38 of 45 (motors, encoders, drivetrain, IMU, rangefinder, timing) |
| **2: Test board + fixtures** | Mount PCB/motors/sensors on board. Fixed wall for rangefinder. Servo-actuated sliding plate for reflectance. | +3 (reflectance white/dark, rangefinder known distance) |
| **3: LED + servo sensors** | Phototransistor over LED. Break-beam at servo arm. | +3 (LED on/off, LED blink, servo sweep) |
| **4: RGB color sensor** | TCS34725 over NeoPixel. | +1 (RGB LED colors) |

### CI pipeline

The GitHub Actions workflow (`.github/workflows/hardware-test.yml`) runs two jobs:

1. **Unit tests** — `ubuntu-latest`, runs `pytest tests/unit/ -v`
2. **Hardware tests** — `self-hosted-xrp-teststand` runner, runs `python scripts/ci_hardware_test.py`

The CI host script (`scripts/ci_hardware_test.py`):
1. Detects Pico via `mpremote connect list`
2. Syncs XRPLib source and test files to the Pico
3. Creates `/teststand_mode` flag file
4. Runs `tests/hardware/run_all_hw_tests.py`
5. Parses JSON results line (`__RESULTS_JSON__:{...}`)
6. Returns exit code 0 (all pass) or 1 (any failure)

---

## Regression Checklist

When making changes, run:

1. All unit tests (`pytest tests/unit/ -v`)
2. If motor/encoder changes: `test_hw_motors.py`, `test_hw_encoders.py`
3. If drivetrain/PID changes: `test_hw_drivetrain.py`
4. If sensor changes: relevant `test_hw_*.py`
5. If timer/IRQ changes: `test_hw_timing.py`
6. Full hardware suite before any release (`run_all_hw_tests.py`)

On the automated test stand, steps 2-6 run automatically on every push to `XRPLib/**` or `tests/hardware/**`.

---

## Known Limitations

- Unit tests mock all hardware; they cannot catch real timing issues, I2C failures, or PIO state machine bugs
- In manual mode, some tests require human observation (LED visual, servo movement)
- In test stand mode (Phase 1), LED/servo/RGB tests verify no-crash only; full sensor verification requires Phases 2-4
- Drivetrain accuracy depends on motor load; test stand motors have no wheels, so distances are encoder-based only
- IMU yaw drift test assumes the board is stationary — vibration from motors on the same test board could affect results
- The `json` module on MicroPython may not be available on all firmware builds; `run_all_hw_tests.py` falls back to print-based output
