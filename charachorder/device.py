from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from .errors import UnknownProduct, UnknownVendor


@dataclass
class CCDevice:
    name: str
    company: Literal["CharaChorder"]
    product: Literal["One", "Lite", "X", "Engine"]
    bootloader_mode: bool
    vendor: Literal["Adafruit", "Espressif"]
    chipset: Literal["M0", "S2"]
    port: str

    def __init__(self, device: ListPortInfo):
        self.company = "CharaChorder"

        known_pids = {
            0x800F: "One",  # M0
            0x801C: "Lite",  # M0
            0x812E: "Lite",  # S2
            0x812F: "Lite",  # S2 - UF2 Bootloader
            0x818B: "X",  # S2
            0x818C: "X",  # S2 - UF2 Bootloader
            0x818D: "X",  # S2 Host
            0x818E: "X",  # S2 Host - UF2 Bootloader
            0x8189: "Engine",  # S2
            0x818A: "Engine",  # S2 - UF2 Bootloader
        }
        if device.pid in known_pids:
            self.name = known_pids[device.pid]
            if device.pid in (0x812F, 0x818C, 0x818E, 0x818A):
                self.bootloader_mode = True
        else:
            raise UnknownProduct(device.pid)

        known_vids = {
            0x239A: ("Adafruit", "M0"),
            0x303A: ("Espressif", "S2"),
        }
        if device.vid in known_vids:
            self.name, self.chipset = known_vids[device.vid]
        else:
            raise UnknownVendor(device.vid)

        self.port = device.device
        self.name = f"{self.company} {self.product} {self.chipset}"

    def __repr__(self):
        return f"{self.name} ({self.port})"

    def __str__(self):
        return f"{self.name} ({self.port})"

    @classmethod
    def list_devices(cls) -> list[CCDevice]:
        return [cls(device) for device in list_ports.comports()]
