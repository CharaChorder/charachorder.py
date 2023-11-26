from __future__ import annotations

from serial.tools import list_ports

from .errors import UnknownDevice


class CCDevice:
    def __init__(self, device):
        self.device = device
        self.serial_port = device.device

        if device.vid == 9114:  # Adafruit (M0)
            if device.pid == 32783:
                self.name = "CharaChorder One"
            elif device.pid == 32796:
                self.name = "CharaChorder Lite (M0)"
            else:
                raise UnknownDevice(device)

        elif device.vid == 12346:  # Espressif (S2)
            if device.pid == 33070:
                self.name = "CharaChorder Lite (S2)"
            elif device.pid == 33163:
                self.name = "CharaChorder X"
            else:
                raise UnknownDevice(device)
        else:
            raise UnknownDevice(device)

    def __repr__(self):
        return f"{self.name} ({self.serial_port})"

    def __str__(self):
        return f"{self.name} ({self.serial_port})"

    @staticmethod
    def list_devices() -> list["CCDevice"]:
        return [CCDevice(device) for device in list_ports.comports()]
