from .device import CCDevice
from .serial import CCSerial


def main():
    for device in CCDevice.list_devices():
        with CCSerial(device) as cc_serial:
            print(cc_serial.execute("ID"))


if __name__ == "__main__":
    main()
