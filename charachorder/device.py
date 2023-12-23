from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from typing_extensions import Self

from serial import Serial
from serial.tools import list_ports

from .errors import (
    SerialConnectionNotFound,
    UnknownCommand,
    UnknownProduct,
    UnknownVendor,
)


pid_mapping = {}
vid_mapping = {
    0x239A: ("Adafruit", "M0"),
    0x303A: ("Espressif", "S2"),
}


def allowed_product_ids(*product_ids: int):
    def decorator(cls):
        for product_id in product_ids:
            pid_mapping[product_id] = cls
        return cls

    return decorator


class Device(NamedTuple):
    product_id: int
    vendor_id: int
    port: str

    @classmethod
    def list_devices(cls) -> list[Self]:
        devices = []
        for port_info in list_ports.comports():
            device = cls(
                product_id=port_info.pid,
                vendor_id=port_info.vid,
                port=port_info.device,
            )
            devices.append(device)
        return devices


class CharaChorder(Device):
    bootloader_mode: bool
    chipset: Literal["M0", "S2"]
    vendor: Literal["Adafruit", "Espressif"]

    def __init__(self, device: Device):
        if device.product_id not in pid_mapping:
            raise UnknownProduct(device.product_id)

        if device.vendor_id in vid_mapping:
            self.name, self.chipset = vid_mapping[device.vendor_id]
        else:
            raise UnknownVendor(device.vendor_id)

        self.name = f"{self.__class__.__name__} {self.chipset}"

    def __repr__(self):
        return f"{self.name} ({self.port})"

    def __str__(self):
        return f"{self.name} ({self.port})"

    @classmethod
    def list_devices(cls) -> list[Self]:
        devices = []
        for device in super().list_devices():
            subclass = pid_mapping.get(device.product_id, cls)
            if issubclass(subclass, cls):
                devices.append(subclass(device))
        return devices

    def open(self):
        self.connection = Serial(self.port, 115200, timeout=1)

    def close(self):
        self.connection.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def execute(self, *args: int | str) -> tuple[str, ...]:
        # TODO: Also detect a "closed" connection object
        if self.connection is None:
            raise SerialConnectionNotFound

        command = " ".join(map(str, args))
        self.connection.write(f"{command}\r\n".encode("utf-8"))
        output = tuple(self.connection.readline().decode("utf-8").strip().split(" "))

        command_from_output = output[: len(args)]
        actual_output = output[len(args) :]

        if command_from_output[0] == "UKN":
            raise UnknownCommand(command)

        return actual_output


@allowed_product_ids(0x800F)  # M0
class CharaChorderOne(CharaChorder):
    pass


@allowed_product_ids(
    0x801C,  # M0
    0x812E,  # S2
    0x812F,  # S2 - UF2 Bootloader
)
class CharaChorderLite(CharaChorder):
    def __init__(self, device: CharaChorder):
        super().__init__(device)
        self.bootloader_mode = self.product_id == 0x812F


@allowed_product_ids(
    0x818B,  # S2
    0x818C,  # S2 - UF2 Bootloader
    0x818D,  # S2 Host
    0x818E,  # S2 Host - UF2 Bootloader
)
class CharaChorderX(CharaChorder):
    def __init__(self, device: CharaChorder):
        super().__init__(device)
        self.bootloader_mode = self.product_id in (0x818C, 0x818E)


@allowed_product_ids(
    0x8189,  # S2
    0x818A,  # S2 - UF2 Bootloader
)
class CharaChorderEngine(CharaChorder):
    def __init__(self, device: CharaChorder):
        super().__init__(device)
        self.bootloader_mode = self.product_id == 0x818A
