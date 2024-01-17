from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable, Generator, Literal, NamedTuple

from serial import Serial
from serial.tools import list_ports

from .errors import (
    InvalidParameter,
    InvalidParameterInput,
    SerialConnectionNotFound,
    UnknownCommand,
    UnknownProduct,
    UnknownVendor,
)
from .types import Chord, ChordPhrase, KeymapCode, OperatingSystem

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
    def list_devices(cls) -> list[Device]:
        devices = []
        for port_info in list_ports.comports():
            device = Device(
                product_id=port_info.pid,
                vendor_id=port_info.vid,
                port=port_info.device,
            )
            devices.append(device)
        return devices


class CharaChorder(Device):
    bootloader_mode: bool
    chordmaps: list[tuple[Chord, ChordPhrase]]
    connection: Serial
    chipset: Literal["M0", "S2"]
    vendor: Literal["Adafruit", "Espressif"]

    def __init__(self, product_id: int, vendor_id: int, port: str):
        self.chordmaps = []
        self.connection = Serial(baudrate=115200, timeout=1)
        # The port is specified separately so that
        # the connection is not immediately opened
        self.connection.port = port

        if product_id not in pid_mapping:
            raise UnknownProduct(product_id)

        if vendor_id in vid_mapping:
            self.name, self.chipset = vid_mapping[vendor_id]
        else:
            raise UnknownVendor(vendor_id)

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
                devices.append(
                    subclass(device.product_id, device.vendor_id, device.port)
                )
        return devices

    def open(self):
        self.connection.open()

    def close(self):
        self.connection.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def execute(self, *args: int | str) -> tuple[str, ...]:
        if self.connection.is_open is False:
            raise SerialConnectionNotFound

        command = " ".join(map(str, args))
        self.connection.write(f"{command}\r\n".encode("utf-8"))
        output = tuple(self.connection.readline().decode("utf-8").strip().split(" "))

        # Drop serial header
        if output[0] == "01":
            output = output[1:]

        if output[0] == "UKN":
            raise UnknownCommand(command)

        return output[len(args) :]

    def get_id(self) -> str:
        return " ".join(self.execute("ID"))

    def get_version(self) -> str:
        return self.execute("VERSION")[0]

    def get_chordmap_count(self) -> int:
        return int(self.execute("CML", "C0")[0])

    def get_chordmap(self, index: int) -> tuple[Chord, ChordPhrase]:
        if index not in range(self.get_chordmap_count()):
            raise IndexError("Chordmap index out of range")

        chord, phrase, success = self.execute("CML", "C1", index)
        return Chord.from_hex(chord), ChordPhrase.from_hex(phrase)

    def get_chordmaps(self) -> Generator[tuple[Chord, ChordPhrase], None, None]:
        chordmap_count = self.get_chordmap_count()
        return (self.get_chordmap(i) for i in range(chordmap_count))

    def populate_chordmaps(
        self,
        *,
        limit: int | None = None,
        manual_interrupt: Callable[[], bool] = lambda: False,
        timeout: float | None = None,
    ) -> tuple[list[tuple[Chord, ChordPhrase]], bool]:
        chordmaps = []
        interrupted = False
        start_time = time.time()
        timed_out = lambda: timeout and time.time() - start_time > timeout

        for index, chordmap in enumerate(self.get_chordmaps()):
            if index == limit:
                break

            if manual_interrupt() or timed_out():
                interrupted = True
                break

            chordmaps.append(chordmap)

        if not interrupted:
            self.chordmaps = chordmaps
        return chordmaps, interrupted

    def get_chord_phrase(self, chord: Chord) -> ChordPhrase | None:
        phrase = self.execute("CML", "C2", chord.to_hex())[0]
        return ChordPhrase.from_hex(phrase) if phrase != "0" else None

    def set_chordmap(self, chord: Chord, phrase: ChordPhrase) -> bool:
        return self.execute("CML", "C3", chord.to_hex(), phrase.to_hex())[0] == "0"

    def delete_chordmap(self, chord: Chord) -> bool:
        return self.execute("CML", "C4", chord.to_hex())[0] == "0"

    def delete_chordmaps(self):
        self.execute("RST", "CLEARCML")

    def upgrade_chordmaps(self):
        self.execute("RST", "UPGRADECML")

    def commit(self) -> bool:
        return self.execute("VAR", "B0")[0] == "0"

    def _maybe_commit(self, success, commit: bool) -> bool:
        if success and commit:
            return self.commit()
        return success

    def get_parameter(self, code: int) -> int:
        value, success = self.execute("VAR", "B1", hex(code))
        if success != "0":
            raise InvalidParameter(hex(code))
        return int(value)

    def set_parameter(
        self, code: int, value: int | str, *, commit: bool = False
    ) -> bool:
        success = self.execute("VAR", "B2", hex(code), value)[0]
        if success != "0":
            # Segregate invalid parameter and invalid input errors
            self.get_parameter(code)
            raise InvalidParameterInput(hex(code), value)
        return self._maybe_commit(success, commit)

    def get_keymap(self, code: KeymapCode, index: int) -> int:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")

        return int(self.execute("VAR", "B3", code.value, index)[0])

    def set_keymap(
        self, code: KeymapCode, index: int, action_id: int, *, commit: bool = False
    ) -> bool:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")
        if action_id not in range(8, 2048):
            raise IndexError("Action id out of range. Must be between 8-2047")

        return self._maybe_commit(
            self.execute("VAR", "B4", code.value, index, action_id)[0] == "0", commit
        )

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

    def append_functional_chords(self):
        self.execute("RST", "FUNC")

    def get_available_ram(self) -> int:
        return int(self.execute("RAM")[0])

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
    def __init__(self, product_id: int, vendor_id: int, port: str):
        super().__init__(product_id, vendor_id, port)
        self.bootloader_mode = self.product_id == 0x812F


@allowed_product_ids(
    0x818B,  # S2
    0x818C,  # S2 - UF2 Bootloader
    0x818D,  # S2 Host
    0x818E,  # S2 Host - UF2 Bootloader
)
class CharaChorderX(CharaChorder):
    def __init__(self, product_id: int, vendor_id: int, port: str):
        super().__init__(product_id, vendor_id, port)
        self.bootloader_mode = self.product_id in (0x818C, 0x818E)


@allowed_product_ids(
    0x8189,  # S2
    0x818A,  # S2 - UF2 Bootloader
)
class CharaChorderEngine(CharaChorder):
    def __init__(self, product_id: int, vendor_id: int, port: str):
        super().__init__(product_id, vendor_id, port)
        self.bootloader_mode = self.product_id == 0x818A
