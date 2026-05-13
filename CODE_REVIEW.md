# XRP MicroPython Library — Code Review

## Bugs

### 1. `return Exception` instead of `raise Exception`
**File:** `XRPLib/encoded_motor.py:62`

```python
return Exception("Invalid motor index")  # returns the exception object silently
```

Should be `raise Exception(...)`. Currently an invalid index silently returns an Exception object as if it were a motor, which will cause a confusing `AttributeError` later when the caller tries to use it.

---

### 2. IMU `gyro_rate()` reads wrong register bits
**File:** `XRPLib/imu.py:484`

```python
index = list(LSM_ODR.values()).index(self.reg_ctrl1_xl_bits.ODR_G)
```

This reads `ODR_G` from `reg_ctrl1_xl_bits` (the **accelerometer** control register) instead of from `reg_ctrl2_g_bits` (the **gyroscope** control register). Should be:

```python
index = list(LSM_ODR.values()).index(self.reg_ctrl2_g_bits.ODR_G)
```

---

### 3. IMU `timer_frequency` not initialized in `__init__`
**File:** `XRPLib/imu.py`

`self.timer_frequency` is only set inside `gyro_rate()` (line 492), but the timer is started in `reset()` -> `_default_config()` -> `gyro_rate('208Hz')`. If `_start_timer()` is ever called before `gyro_rate()` completes (e.g. in a subclass override or future refactor), you get an `AttributeError`. It should be initialized in `__init__` or `_reset_member_variables()`.

---

### 4. `Timeout` and IMU use raw `ticks_ms` arithmetic instead of `ticks_diff`
**Files:** `XRPLib/timeout.py:23`, `XRPLib/imu.py:184`, `XRPLib/imu.py:514`

```python
# timeout.py:23
return time.ticks_ms() - self.start_time > self.timeout

# imu.py:184
while time.ticks_ms() < (t0 + wait_timeout_ms):

# imu.py:514
while time.ticks_ms() < start_time + calibration_time*1000:
```

`ticks_ms()` wraps around (it's a 30-bit counter on MicroPython). All of these should use `time.ticks_diff(time.ticks_ms(), start_time)` to handle wraparound correctly. These will malfunction if `ticks_ms` wraps during operation (~12.4 days on RP2040).

---

### 5. `_getregs` allocates on the heap inside timer callback
**File:** `XRPLib/imu.py:108-111`

```python
def _getregs(self, reg, num_bytes):
    rx_buf = bytearray(num_bytes)  # heap allocation every call
```

`_update_imu_readings()` is called from a timer callback and calls `get_gyro_rates()` -> `_getregs()`, which allocates a new `bytearray(6)` every call (~208 times/second). In MicroPython timer callbacks, heap allocation can trigger GC and cause crashes or unpredictable timing. Should use a pre-allocated buffer.

---

### 6. I2C operations in timer callback context
**File:** `XRPLib/imu.py:548-553`

The `_update_imu_readings` callback does I2C reads (`readfrom_mem_into`). I2C is a slow bus protocol. MicroPython's soft timers (Timer -1) do run in a thread-safe context (not hard IRQ), so this *works*, but it blocks other soft timer callbacks (like motor speed updates at 50 Hz) for the duration of the I2C transaction. Consider using `micropython.schedule()` to defer this work.

---

## Concurrency / Race Conditions

### 7. Shared mutable `irq_v` array without protection
**File:** `XRPLib/imu.py:82`

`get_acc_rates()`, `get_gyro_rates()`, and `get_acc_gyro_rates()` all write to `self.irq_v` and return it. The timer callback also calls `get_gyro_rates()` which mutates `irq_v[1]`. If user code calls `get_acc_gyro_rates()` while the timer fires, the gyro values in the returned array could be partially overwritten. The returned list is a shared reference, not a copy.

---

### 8. Rangefinder `_trigger_ping` does busy-wait in timer callback
**File:** `XRPLib/rangefinder.py:92-116`

The timer callback calls `_trigger_ping()` which does a busy-wait `_delay_us(10)`. Timer callbacks with `Timer(-1)` are soft callbacks on RP2040, but the ~15us busy-wait still blocks other callbacks. If the platform treats virtual timers as hard IRQs, the busy loop could cause watchdog issues.

---

### 9. Rangefinder floating-point division in hard IRQ
**File:** `XRPLib/rangefinder.py:134`

```python
self.cms = (pulse_time / 2) / 29.1
```

The echo handler runs as a pin IRQ (hard IRQ). Floating-point division can allocate on the heap in MicroPython. Consider using integer arithmetic instead:

```python
self.cms = pulse_time * 100 // 5820  # equivalent to pulse_time / 2 / 29.1
```

---

## Design Issues

### 10. `defaults.py` eagerly initializes all hardware
**File:** `XRPLib/defaults.py:18-29`

Importing `defaults` creates ALL hardware objects including all 4 motors, the IMU (with 1-second calibration!), the rangefinder, servos, and webserver. Most programs only need 2 motors + drivetrain. This wastes:
- 1 second on IMU calibration every boot
- 4 PIO state machines (only 4 available per PIO block)
- 4 virtual timers for motor speed control (motors 3 & 4 usually unused)
- Rangefinder timer running continuously even when not needed

Consider lazy initialization or splitting into separate import targets.

---

### 11. Motor PWM frequency of 50 Hz is very low
**Files:** `XRPLib/motor.py:17`, `XRPLib/motor.py:63-64`

50 Hz PWM means the motor duty cycle only updates every 20ms and produces audible whine. Typical DC motor PWM is 1-20 kHz. 50 Hz is the standard for servo control, not DC motors. This likely causes jerky low-speed performance and audible noise.

---

### 12. Encoder `get_position_counts` reads PIO FIFO 5 times (blocking)
**File:** `XRPLib/encoder.py:47-52`

```python
counts = self.sm.get()
counts = self.sm.get()
counts = self.sm.get()
counts = self.sm.get()
counts = self.sm.get()
```

This is called from the 50 Hz motor update timer callback. Each `sm.get()` blocks until data is in the FIFO. The PIO RX FIFO is 4 deep, so 5 reads drains the buffer and gets the freshest value. However, this is a blocking operation in a timer callback, which could cause timing jitter for other callbacks.

---

### 13. PID `min_output` creates oscillation around setpoint
**File:** `XRPLib/pid.py:94-98`

```python
if output > 0:
    output = max(self.min_output, output)
else:
    output = min(-self.min_output, output)
```

The output can NEVER be between `-min_output` and `+min_output` (excluding zero). When the error is very small, the output jumps between `+min_output` and `-min_output`, causing visible oscillation around the setpoint. The system only stops via the `is_done()` tolerance check in the calling code (`straight()`, `turn()`), but the robot will visibly jerk back and forth before stopping.

---

### 14. PID never outputs zero
Related to issue #13. Since `min_output` forces the output to always be at least `+/-min_output`, the PID can never output 0. The system only stops via the `is_done()` tolerance check in calling code. If someone uses PID standalone without checking `is_done()`, the motors never stop.

---

### 15. No cleanup/deinitialization for Rangefinder instances
**File:** `XRPLib/rangefinder.py:89`

`_instances` is a class-level list that's never cleaned up. If a Rangefinder is garbage collected, it stays in `_instances`, and the timer callback will try to call `_do_ping` on a dead object. There's no `deinit()` method to remove the instance or stop the timer.

---

## Memory & Performance

### 16. String concatenation in `_generateHTML`
**File:** `XRPLib/webserver.py:234-258`

Building HTML via repeated `string +=` creates many intermediate string objects. On a memory-constrained microcontroller, this can fragment the heap and trigger GC during request handling. Consider using a list and `''.join()`:

```python
parts = [_HTML1]
# ... append to parts ...
return ''.join(parts)
```

---

### 17. `_raw_to_mg` and `_raw_to_mdps` receive sliced bytearrays
**File:** `XRPLib/imu.py:137-141`

```python
def _raw_to_mg(self, raw):
    return self._int16((raw[1] << 8) | raw[0]) * LSM_MG_PER_LSB_2G * self._acc_scale_factor
```

Called with `raw_bytes[0:2]` which creates a new `bytearray` slice each time. In the timer callback path, this means 3 allocations per update (~208 Hz). Pass buffer and index instead of slicing.

---

## Minor Issues

### 18. Typo: `ZERO_EFFORT_BREAK` should be `BRAKE`
**File:** `XRPLib/encoded_motor.py:10`

```python
ZERO_EFFORT_BREAK = True   # typo: should be ZERO_EFFORT_BRAKE
```

---

### 19. `webserver.py` creates a module-level instance with side effects
**File:** `XRPLib/webserver.py:261`

The `webserver = Webserver()` at module level runs `gc.threshold(50000)` on import. This side effect happens even if you only import the class for type checking or introspection.

---

### 20. Reflectance `MAX_ADC_VALUE` off by one
**File:** `XRPLib/reflectance.py:29`

```python
self.MAX_ADC_VALUE: int = 65536
```

The max value from `read_u16()` is 65535, so the sensor can never return exactly 1.0 (max is `65535/65536 = 0.99998`). Should be `65535` if a true [0, 1] range is desired.

---

### 21. `DualPWMMotor.set_effort` doesn't clamp input
**File:** `XRPLib/motor.py:66-80`

Unlike `SinglePWMMotor` which clamps effort to [0, 1], `DualPWMMotor` passes `abs(effort)` directly to `duty_u16()`. An effort > 1.0 would produce PWM values > 65535, which may wrap or error.

---

### 22. IMU `is_connected()` check is ignored
**File:** `XRPLib/imu.py:56-58`

```python
if not self.is_connected():
    # TODO - do somehting intelligent here
    pass
```

If the IMU isn't connected, the code proceeds to `reset()` which will fail with an I2C error. Should raise an exception or return a null/dummy IMU.

---

## Suggestions for Improvement

- **Add a `deinit()` pattern** to all hardware classes (rangefinder, motors, IMU) to cleanly stop timers and release pins. Critical for REPL-based development where students restart code frequently.
- **Consider `micropython.schedule()`** for the IMU timer callback to avoid doing I2C in interrupt context.
- **Pre-allocate all buffers** used in timer/IRQ callbacks (especially the 6-byte and 12-byte reads in IMU).
- **Make `defaults.py` lazy** — use properties or functions so unused hardware isn't initialized.
- **Increase motor PWM frequency** to at least 1 kHz for smoother motor operation.
- **Add bounds checking** in `DualPWMMotor.set_effort` to match `SinglePWMMotor`.
