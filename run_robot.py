import os
import shutil
from ampy.files import Files
from ampy.pyboard import Pyboard
import serial, threading, time, subprocess
import serial.tools.list_ports
import filecmp


# Folder to store the last synced XRPLib files
TEMP_FOLDER = ".temp_xrplib"


def ensure_directory_exists(files, directory):
    """Ensure that a directory exists on the Pico. If not, create it."""
    try:
        if directory != "/":  # Root directory always exists
            files.mkdir(directory)
            print(f"Directory {directory} created on Pico.")
    except Exception as e:
        # Ignore the error if the directory already exists
        pass

def copy_file_to_pico(files, local_file_path, pico_destination_path):
    """Copy a single file to the Pico, replacing it if it already exists."""
    try:
        with open(local_file_path, 'rb') as local_file:
            file_content = local_file.read()
        
        # Write or replace the file on the Pico
        files.put(pico_destination_path, file_content)
        print(f"Successfully copied {local_file_path} to {pico_destination_path} on Pico.")
        
    except Exception as e:
        print(f"Failed to copy file {local_file_path}. Error: {str(e)}")

def copy_directory_to_pico(files, local_directory, pico_destination_directory):
    """Copy an entire directory to the Pico, including all subdirectories and files"""
    try:
        for root, dirs, files_list in os.walk(local_directory):
            relative_path = os.path.relpath(root, local_directory)
            pico_dir_path = os.path.join(pico_destination_directory, relative_path).replace("\\", "/")
            ensure_directory_exists(files, pico_dir_path)
            
            for file_name in files_list:
                local_file_path = os.path.join(root, file_name)
                pico_file_path = os.path.join(pico_dir_path, file_name).replace("\\", "/")
                copy_file_to_pico(files, local_file_path, pico_file_path)
        
    except Exception as e:
        print(f"Failed to copy directory {local_directory}. Error: {str(e)}")
    finally:
        pyb.close()  # Ensure the connection to the Pico is closed

def create_temp_folder():
    """Create a temporary folder to store the last synced XRPLib files."""
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

def compare_and_copy(files, local_directory, pico_destination_directory):
    """Compare local XRPLib with the last synced version and copy only changed files."""
    create_temp_folder()
    for root, dirs, files_list in os.walk(local_directory):
        relative_path = os.path.relpath(root, local_directory)
        pico_dir_path = os.path.join(pico_destination_directory, relative_path).replace("\\", "/")
        temp_dir_path = os.path.join(TEMP_FOLDER, relative_path)

        if not os.path.exists(temp_dir_path):
            os.makedirs(temp_dir_path)
        
        for file_name in files_list:
            local_file_path = os.path.join(root, file_name)
            temp_file_path = os.path.join(temp_dir_path, file_name)
            pico_file_path = os.path.join(pico_dir_path, file_name).replace("\\", "/")

            if not os.path.exists(temp_file_path) or not filecmp.cmp(local_file_path, temp_file_path, shallow=False):
                # If the file doesn't exist in the temp folder, or it has changed, copy it
                copy_file_to_pico(files, local_file_path, pico_file_path)
                # Update the temp folder with the new file
                shutil.copy2(local_file_path, temp_file_path)

def read_serial_output(port, baudrate=115200, timeout=1):
    """Read and print serial output from the Pico W."""
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print("Reading serial output...")
            while True:
                if ser.in_waiting > 0:
                    output = ser.read(ser.in_waiting).decode('utf-8')
                    print(output, end='')  # Print without adding extra newlines
                time.sleep(0.1)  # Small delay to prevent high CPU usage
    except Exception as e:
        print(f"Failed to read serial output. Error: {str(e)}")

def run_pico_script(port, script_name):
    """Run a MicroPython script on the Pico using ampy."""
    try:
        subprocess.run(['ampy', '-p', port, 'run', script_name], check=True)
        print(f"Successfully ran {script_name} on Pico.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run script {script_name}. Error: {str(e)}")

def list_files_on_pico(port):
    """List all files and folders on the Pico."""
    try:
        pyb = Pyboard(port)
        files = Files(pyb)
        file_list = files.ls('/')
        
        print("Files and folders on Pico:")
        for file in file_list:
            print(file)
        
    except Exception as e:
        print(f"Failed to list files. Error: {str(e)}")

def copy_all_files_to_pico(port, directory=True, main=True, telemetry=True):
    pyb = Pyboard(port)
    files = Files(pyb)
    
    if directory:
        compare_and_copy(files, "XRPLib", "lib/XRPLib")
    if main:
        copy_file_to_pico(files, "main.py", "main.py")
    if telemetry:
        copy_file_to_pico(files, "telemetry.txt", "telemetry.txt")

def detect_pico_port():
    """Auto-detect the Pico W's serial port."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "usbmodem" in port.device or "COM" in port.device:  # Adjust this pattern if needed
            return port.device
    raise IOError("Pico W not found. Please check the connection.")

if __name__ == "__main__":

    # Auto-detect the Pico W port
    pico_port = detect_pico_port()
    print(f"Pico W detected on port: {pico_port}")

    # Copy any changed files to the Pico
    copy_all_files_to_pico(pico_port)

    # Run the main.py script on the Pico
    run_pico_script(pico_port, "main.py")
