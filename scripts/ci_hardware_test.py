#!/usr/bin/env python3
"""
CI host-side script for running hardware tests on an XRP test stand.

This script runs on the CI host machine (not on the Pico). It:
1. Detects the Pico's serial port
2. Syncs the XRPLib code to the Pico
3. Creates the /teststand_mode flag file
4. Uploads and runs the hardware test suite
5. Parses results and returns appropriate exit code

Prerequisites:
    pip install mpremote

Usage:
    python scripts/ci_hardware_test.py
"""
import subprocess
import sys
import json
import re
import os


def run_cmd(args, check=True, capture=True):
    """Run a command and return its output."""
    print(f"  > {' '.join(args)}")
    result = subprocess.run(
        args,
        capture_output=capture,
        text=True,
        timeout=300,  # 5 minute timeout
    )
    if check and result.returncode != 0:
        print(f"  STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(args)}")
    return result


def detect_pico():
    """Verify mpremote can see a connected Pico."""
    result = run_cmd(["mpremote", "connect", "list"])
    if result.stdout.strip():
        print(f"  Detected devices:\n{result.stdout}")
        return True
    else:
        print("  No Pico detected!")
        return False


def sync_xrplib():
    """Copy XRPLib source files to the Pico's lib directory."""
    print("\nSyncing XRPLib to Pico...")
    # Create lib/XRPLib directory on Pico
    run_cmd(["mpremote", "mkdir", ":lib"], check=False)
    run_cmd(["mpremote", "mkdir", ":lib/XRPLib"], check=False)

    # Copy all .py files from XRPLib/
    xrplib_dir = os.path.join(os.path.dirname(__file__), "..", "XRPLib")
    for filename in os.listdir(xrplib_dir):
        if filename.endswith(".py"):
            src = os.path.join(xrplib_dir, filename)
            dst = f":lib/XRPLib/{filename}"
            run_cmd(["mpremote", "cp", src, dst])
    print("  XRPLib synced.")


def sync_test_files():
    """Copy hardware test files to the Pico."""
    print("\nSyncing test files to Pico...")
    run_cmd(["mpremote", "mkdir", ":tests"], check=False)
    run_cmd(["mpremote", "mkdir", ":tests/hardware"], check=False)

    test_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "hardware")
    for filename in os.listdir(test_dir):
        if filename.endswith(".py"):
            src = os.path.join(test_dir, filename)
            dst = f":tests/hardware/{filename}"
            run_cmd(["mpremote", "cp", src, dst])
    print("  Test files synced.")


def ensure_teststand_mode():
    """Create the /teststand_mode flag file on the Pico."""
    print("\nSetting teststand mode...")
    run_cmd(["mpremote", "exec", "f = open('/teststand_mode', 'w'); f.close()"])
    print("  Teststand mode enabled.")


def run_tests():
    """Run the hardware test suite and capture output."""
    print("\nRunning hardware tests...")
    print("-" * 50)

    result = run_cmd(
        ["mpremote", "run", "tests/hardware/run_all_hw_tests.py"],
        check=False,
    )

    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")

    return result


def parse_results(output):
    """Parse the JSON results line from test output."""
    for line in output.split("\n"):
        if line.startswith("__RESULTS_JSON__:"):
            json_str = line[len("__RESULTS_JSON__:"):]
            return json.loads(json_str)
    return None


def main():
    print("XRP Hardware Test CI Runner")
    print("=" * 50)

    # Step 1: Detect Pico
    print("\nDetecting Pico...")
    if not detect_pico():
        print("\nFAIL: No Pico W detected. Check USB connection.")
        sys.exit(1)

    # Step 2: Sync code
    sync_xrplib()
    sync_test_files()

    # Step 3: Enable teststand mode
    ensure_teststand_mode()

    # Step 4: Run tests
    result = run_tests()

    # Step 5: Parse and report
    print("\n" + "=" * 50)
    results = parse_results(result.stdout)

    if results is None:
        print("FAIL: Could not parse test results from output.")
        sys.exit(1)

    total = results["total_passed"] + results["total_failed"]
    print(f"Final: {results['total_passed']}/{total} tests passed")

    if results["total_failed"] > 0:
        print(f"\n{results['total_failed']} test(s) FAILED:")
        for mod in results["modules"]:
            if mod["failed"] > 0 or mod["error"]:
                print(f"  - {mod['name']}: {mod['failed']} failed")
                if mod["error"]:
                    print(f"    Error: {mod['error']}")
        sys.exit(1)
    else:
        print("\nAll tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
