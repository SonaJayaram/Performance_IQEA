import subprocess

def get_connected_devices():
    try:
        result = subprocess.check_output("adb devices", shell=True).decode()
        lines = result.strip().split("\n")[1:]
        devices = [line.split("\t")[0] for line in lines if "device" in line]
        return devices
    except:
        return []