from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

from serial import Serial
from serial.tools import list_ports

from .errors import (
    SerialConnectionNotFound,
    UnknownCommand,
    UnknownProduct,
    UnknownVendor,
)
from .types import KeymapCode, ParameterCode

if TYPE_CHECKING:
    from typing_extensions import Self

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

    # ID
    def get_id(self) -> str:
        return " ".join(self.execute("ID"))

    # VERSION
    def get_version(self) -> str:
        return self.execute("VERSION")[0]

    # CML

    def get_chordmap_count(self) -> int:
        return int(self.execute("CML", "C0")[0])

    def get_chordmap_by_index(self, index: int) -> tuple[str, str]:
        if index not in range(self.get_chordmap_count()):
            raise IndexError("Chordmap index out of range")

        chord, chordmap, success = self.execute("CML", "C1", index)
        return chord, chordmap

    def get_chordmap_by_chord(self, chord: str) -> str | None:
        chordmap = self.execute("CML", "C2", chord)[0]
        return chordmap if chordmap != "0" else None

    def set_chordmap_by_chord(self, chord: str, chordmap: str) -> bool:
        return self.execute("CML", "C3", chord, chordmap)[0] == "0"

    def del_chordmap_by_chord(self, chord: str) -> bool:
        return self.execute("CML", "C4", chord)[0] == "0"

    # VAR

    def commit(self) -> bool:
        return self.execute("VAR", "B0")[0] == "0"

    def get_parameter(self, code: ParameterCode) -> int:
        # TODO: enforce checking device-specific codes
        return int(self.execute("VAR", "B1", code.value)[0])

    def set_parameter(self, code: ParameterCode, value: int) -> bool:
        # TODO: validate value
        return self.execute("VAR", "B2", code.value, value)[0] == "0"

    def get_keymap(self, code: KeymapCode, index: int) -> int:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")

        return int(self.execute("VAR", "B3", code.value, index)[0])

    def set_keymap(self, code: KeymapCode, index: int, action_id: int) -> bool:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")
        if action_id not in range(8, 2048):
            raise IndexError("Action id out of range. Must be between 8-2047")

        return self.execute("VAR", "B4", code.value, index, action_id)[0] == "0"

    # RST

    def restart(self):
        self.execute("RST")

    def factory_reset(self):
        self.execute("RST", "FACTORY")

    def enter_bootloader_mode(self):
        self.execute("RST", "BOOTLOADER")

    def reset_parameters(self):
        self.execute("RST", "PARAMS")

    def reset_keymaps(self):
        self.execute("RST", "KEYMAPS")

    def append_starter_chords(self):
        self.execute("RST", "STARTER")

    def nuke_chordmaps(self):
        self.execute("RST", "CLEARCML")

    def upgrade_chordmaps(self):
        self.execute("RST", "UPGRADECML")

    def append_functional_chords(self):
        self.execute("RST", "FUNC")

    # RAM
    def get_available_ram(self) -> int:
        return int(self.execute("RAM")[0])

    # SIM
    def sim(self, subcommand: str, value: str) -> str:
        return self.execute("SIM", subcommand, value)[0]


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
