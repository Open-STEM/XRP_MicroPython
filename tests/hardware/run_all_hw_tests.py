"""
Master test runner for all hardware integration tests.
Runs each test module sequentially and outputs a JSON summary.

Usage:
    mpremote run tests/hardware/run_all_hw_tests.py

In teststand mode (file /teststand_mode exists on Pico), all tests
run without manual intervention.
"""
import sys
import time
import json

# Test modules to run, in order
TEST_MODULES = [
    ("Board", "test_hw_board"),
    ("Motors", "test_hw_motors"),
    ("Encoders", "test_hw_encoders"),
    ("Drivetrain", "test_hw_drivetrain"),
    ("Rangefinder", "test_hw_rangefinder"),
    ("Reflectance", "test_hw_reflectance"),
    ("IMU", "test_hw_imu"),
    ("Servo", "test_hw_servo"),
    ("Timing", "test_hw_timing"),
]

results = {
    "total_passed": 0,
    "total_failed": 0,
    "modules": [],
}


def run_module(name, module_name):
    """
    Run a test module by importing it. Each module prints its own
    PASS/FAIL lines and sets module-level `passed` and `failed` counters.
    """
    print()
    print(f"{'='*50}")
    print(f"Running: {name}")
    print(f"{'='*50}")

    module_result = {
        "name": name,
        "module": module_name,
        "passed": 0,
        "failed": 0,
        "error": None,
    }

    try:
        # Each test module runs its tests on import (top-level code)
        mod = __import__(module_name)
        module_result["passed"] = getattr(mod, "passed", 0)
        module_result["failed"] = getattr(mod, "failed", 0)
    except Exception as e:
        module_result["error"] = str(e)
        module_result["failed"] = 1
        print(f"  ERROR: {e}")

    results["total_passed"] += module_result["passed"]
    results["total_failed"] += module_result["failed"]
    results["modules"].append(module_result)

    return module_result["failed"] == 0 and module_result["error"] is None


# Check teststand mode
try:
    from teststand import is_teststand
    mode = "TESTSTAND" if is_teststand() else "MANUAL"
except ImportError:
    mode = "MANUAL"

print(f"XRP Hardware Test Runner — Mode: {mode}")
print(f"Started at: {time.time()}")

all_passed = True
for name, module_name in TEST_MODULES:
    if not run_module(name, module_name):
        all_passed = False

# Print summary
print()
print("=" * 50)
print("SUMMARY")
print("=" * 50)
for mod in results["modules"]:
    status = "PASS" if mod["failed"] == 0 and mod["error"] is None else "FAIL"
    detail = f'{mod["passed"]} passed, {mod["failed"]} failed'
    if mod["error"]:
        detail += f' (ERROR: {mod["error"]})'
    print(f"  [{status}] {mod['name']}: {detail}")

print()
print(f"Total: {results['total_passed']} passed, {results['total_failed']} failed")

# Output machine-readable JSON on a tagged line for CI parsing
print()
print(f"__RESULTS_JSON__:{json.dumps(results)}")

# Exit with appropriate code
if not all_passed:
    sys.exit(1)
