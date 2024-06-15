from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable, Generator, Literal, NamedTuple

from serial import Serial, serialutil
from serial.tools import list_ports

from .errors import (
    InvalidParameter,
    InvalidParameterInput,
    ReconnectTimeout,
    RestartFailure,
    SerialConnectionNotFound,
    TooManyDevices,
    UnknownCommand,
    UnknownProduct,
    UnknownVendor,
)
from .types import Chord, ChordPhrase, Keymap, OperatingSystem

if TYPE_CHECKING:
    from typing_extensions import Self

logger = logging.getLogger(__name__)

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
            self.vendor, self.chipset = vid_mapping[vendor_id]
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
            subclass = pid_mapping.get(device.product_id)
            if subclass and issubclass(subclass, cls):
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

    def ping(self, *, silent: bool = False, timeout: float | None = 10.0):
        if self.connection.is_open is False:
            raise SerialConnectionNotFound

        logger.debug(f"[{self}]: Attempting to ping...")

        start_time = time.time()
        while True:
            try:
                self.connection.write(f"CMD\r\n".encode("utf-8"))
            except serialutil.SerialException:
                logger.debug(f"[{self}]: Not found. Trying to reconnect...")
                elapsed_time = time.time() - start_time
                self._reconnect(timeout=timeout - elapsed_time if timeout else None)
                continue

            if self.connection.readline():
                logger.debug(
                    f"[{self}]: Ping successful in {(time.time() - start_time) * 1000:.2f}ms"
                )
                break

        if not silent:
            print("Pong!")

    def _execute(self, *args: int | str) -> tuple[str, ...]:
        self.ping(silent=True)

        command = " ".join(map(str, args))
        logger.debug(f"[{self}]: Executing '{command}'...")
        self.connection.write(f"{command}\r\n".encode("utf-8"))

        output = []
        for output_bytes in self.connection.iread_until():  # Avoid logs/debug messages
            output = output_bytes.decode("utf-8").strip().split(" ")

            # Drop serial header
            if output[0] == "01":
                output = output[1:]

            if output[0] == "UKN":
                raise UnknownCommand(command)

            if command == " ".join(output[: len(args)]):
                break

        logger.debug(f"[{self}]: Received '{' '.join(output)}'")
        return tuple(output[len(args) :])

    def _reconnect(self, *, timeout: float | None = 3.0):
        def is_same_device(product_id: int, vendor_id: int) -> bool:
            return product_id == self.product_id and vendor_id == self.vendor_id

        start_time = time.time()
        while time.time() - start_time < (timeout or float("inf")):
            try:
                ports = list_ports.comports()
            except TypeError:
                # Weirdly, the list_ports.comports() can fail during the device restart
                #
                # Traceback (most recent call last):
                # ... snip ...
                # File ".../serial/tools/list_ports_linux.py", line 102, in comports
                #     for info in [SysFS(d) for d in devices]
                # File ".../serial/tools/list_ports_linux.py", line 102, in <listcomp>
                #     for info in [SysFS(d) for d in devices]
                # File ".../serial/tools/list_ports_linux.py", line 52, in __init__
                #     self.vid = int(self.read_line(self.usb_device_path, 'idVendor'), 16)
                # TypeError: int() can't convert non-string with explicit base
                continue

            comports = [port for port in ports if is_same_device(port.pid, port.vid)]

            # Device is disconnected or restarting
            if len(comports) == 0:
                continue

            # Device found
            elif len(comports) == 1:
                port = comports[0].device

                # This is true when the device is
                # restarting but hasn't fully shutdown yet
                is_same_session = port == self.port
                if is_same_session:
                    continue

                self.connection.close()
                self.connection.port = port
                try:
                    self.connection.open()
                except serialutil.SerialException:
                    # There is a brief period after the device
                    # restarts where you cannot open a connection to it
                    continue

                break

            # More than one device of the same model was found
            elif len(comports) > 1:
                raise TooManyDevices
        else:
            raise ReconnectTimeout

    def get_commands(self) -> list[str]:
        return self._execute("CMD")[0].split(",")

    def get_id(self) -> str:
        return " ".join(self._execute("ID"))

    def get_version(self) -> str:
        return self._execute("VERSION")[0]

    def get_chordmap_count(self) -> int:
        return int(self._execute("CML", "C0")[0])

    def get_chordmap(self, index: int) -> tuple[Chord, ChordPhrase]:
        if index not in range(self.get_chordmap_count()):
            raise IndexError("Chordmap index out of range")

        chord, phrase, success = self._execute("CML", "C1", index)
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
        phrase = self._execute("CML", "C2", chord.to_hex())[0]
        return ChordPhrase.from_hex(phrase) if phrase != "0" else None

    def set_chordmap(self, chord: Chord, phrase: ChordPhrase) -> bool:
        return self._execute("CML", "C3", chord.to_hex(), phrase.to_hex())[0] == "0"

    def delete_chordmap(self, chord: Chord) -> bool:
        return self._execute("CML", "C4", chord.to_hex())[0] == "0"

    def delete_chordmaps(self):
        self._execute("RST", "CLEARCML")

    def upgrade_chordmaps(self):
        self._execute("RST", "UPGRADECML")

    def append_starter_chordmaps(self):
        self._execute("RST", "STARTER")

    def append_functional_chordmaps(self):
        self._execute("RST", "FUNC")

    def commit(self) -> bool:
        return self._execute("VAR", "B0")[0] == "0"

    def _maybe_commit(self, success, commit: bool) -> bool:
        if success and commit:
            return self.commit()
        return success

    def get_parameter(self, code: int) -> int:
        value, success = self._execute("VAR", "B1", hex(code))
        if success != "0":
            raise InvalidParameter(hex(code))
        return int(value)

    def is_serial_header_enabled(self) -> bool:
        return bool(self.get_parameter(0x01))

    def is_serial_logging_enabled(self) -> bool:
        return bool(self.get_parameter(0x02))

    def is_serial_debugging_enabled(self) -> bool:
        return bool(self.get_parameter(0x03))

    def is_serial_raw_enabled(self) -> bool:
        return bool(self.get_parameter(0x04))

    def is_serial_chord_enabled(self) -> bool:
        return bool(self.get_parameter(0x05))

    def is_serial_keyboard_enabled(self) -> bool:
        return bool(self.get_parameter(0x06))

    def is_serial_mouse_enabled(self) -> bool:
        return bool(self.get_parameter(0x07))

    def is_usb_hid_keyboard_enabled(self) -> bool:
        return bool(self.get_parameter(0x11))

    def is_charachter_entry_enabled(self) -> bool:
        return bool(self.get_parameter(0x12))

    def get_key_scan_duration(self) -> int:
        return self.get_parameter(0x14)

    def get_key_debounce_press_duration(self) -> int:
        return self.get_parameter(0x15)

    def get_key_debounce_release_duration(self) -> int:
        return self.get_parameter(0x16)

    def get_keyboard_output_character_microsecond_delays(self) -> int:
        return self.get_parameter(0x17)

    def is_usb_hid_mouse_enabled(self) -> bool:
        return bool(self.get_parameter(0x21))

    def get_slow_mouse_poll_rate(self) -> int:
        return self.get_parameter(0x22)

    def get_fast_mouse_poll_rate(self) -> int:
        return self.get_parameter(0x23)

    def is_active_mouse_enabled(self) -> bool:
        return bool(self.get_parameter(0x24))

    def get_mouse_scroll_speed(self) -> int:
        return self.get_parameter(0x25)

    def get_mouse_poll_duration(self) -> int:
        return self.get_parameter(0x26)

    def is_chording_enabled(self) -> bool:
        return bool(self.get_parameter(0x31))

    def is_chording_character_counter_timeout_enabled(self) -> bool:
        return bool(self.get_parameter(0x32))

    def get_chording_character_counter_timeout_timer(self) -> int:
        return self.get_parameter(0x33)

    def get_chord_detection_press_tolerance(self) -> int:
        return self.get_parameter(0x34)

    def get_chord_detection_release_tolerance(self) -> int:
        return self.get_parameter(0x35)

    def is_spurring_enabled(self) -> bool:
        return bool(self.get_parameter(0x41))

    def is_spurring_character_counter_timeout_enabled(self) -> bool:
        return bool(self.get_parameter(0x42))

    def get_spurring_character_counter_timeout_timer(self) -> int:
        return self.get_parameter(0x43)

    def is_arpeggiates_enabled(self) -> bool:
        return bool(self.get_parameter(0x51))

    def get_arpeggiate_tolerance(self) -> int:
        return self.get_parameter(0x54)

    def is_compound_chording_enabled(self) -> bool:
        return bool(self.get_parameter(0x61))

    def get_compound_tolerance(self) -> int:
        return self.get_parameter(0x64)

    def get_operating_system(self) -> OperatingSystem:
        return OperatingSystem(self.get_parameter(0x91))

    def is_realtime_feedback_enabled(self) -> bool:
        return bool(self.get_parameter(0x92))

    def is_startup_message_enabled(self) -> bool:
        return bool(self.get_parameter(0x93))

    def set_parameter(
        self, code: int, value: int | str, *, commit: bool = False
    ) -> bool:
        success = self._execute("VAR", "B2", hex(code), value)[0]
        if success != "0":
            # Segregate invalid parameter and invalid input errors
            self.get_parameter(code)
            raise InvalidParameterInput(hex(code), value)
        return self._maybe_commit(success, commit)

    def enable_serial_header(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x01, 1), commit)

    def disable_serial_header(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x01, 0), commit)

    def enable_serial_logging(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x02, 1), commit)

    def disable_serial_logging(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x02, 0), commit)

    def enable_serial_debugging(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x03, 1), commit)

    def disable_serial_debugging(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x03, 0), commit)

    def enable_serial_raw(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x04, 1), commit)

    def disable_serial_raw(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x04, 0), commit)

    def enable_serial_chord(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x05, 1), commit)

    def disable_serial_chord(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x05, 0), commit)

    def enable_serial_keyboard(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x06, 1), commit)

    def disable_serial_keyboard(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x06, 0), commit)

    def enable_serial_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x07, 1), commit)

    def disable_serial_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x07, 0), commit)

    def enable_usb_hid_keyboard(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x11, 1), commit)

    def disable_usb_hid_keyboard(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x11, 0), commit)

    def enable_charachter_entry(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x12, 1), commit)

    def disable_charachter_entry(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x12, 0), commit)

    def set_key_scan_duration(self, value: int, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x14, value), commit)

    def set_key_debounce_press_duration(
        self, value: int, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x15, value), commit)

    def set_key_debounce_release_duration(
        self, value: int, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x16, value), commit)

    def set_keyboard_output_character_microsecond_delays(
        self, value: int = 480, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x17, value), commit)

    def enable_usb_hid_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x21, 1), commit)

    def disable_usb_hid_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x21, 0), commit)

    def set_slow_mouse_poll_rate(self, value: int = 5, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x22, value), commit)

    def set_fast_mouse_poll_rate(
        self, value: int = 25, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x23, value), commit)

    def enable_active_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x24, 1), commit)

    def disable_active_mouse(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x24, 0), commit)

    def set_mouse_scroll_speed(self, value: int = 1, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x25, value), commit)

    def set_mouse_poll_duration(self, value: int = 20, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x26, value), commit)

    def enable_chording(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x31, 1), commit)

    def disable_chording(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x31, 0), commit)

    def enable_chording_character_counter_timeout(
        self, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x32, 1), commit)

    def disable_chording_character_counter_timeout(
        self, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x32, 0), commit)

    def set_chording_character_counter_timeout_timer(
        self, value: int = 40, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x33, value), commit)

    def set_chord_detection_press_tolerance(
        self, value: int, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x34, value), commit)

    def set_chord_detection_release_tolerance(
        self, value: int, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x35, value), commit)

    def enable_spurring(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x41, 1), commit)

    def disable_spurring(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x41, 0), commit)

    def enable_spurring_character_counter_timeout(
        self, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x42, 1), commit)

    def disable_spurring_character_counter_timeout(
        self, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x42, 0), commit)

    def set_spurring_character_counter_timeout_timer(
        self, value: int = 240, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x43, value), commit)

    def enable_arpeggiates(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x51, 1), commit)

    def disable_arpeggiates(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x51, 0), commit)

    def set_arpeggiate_tolerance(
        self, value: int = 800, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x54, value), commit)

    def enable_compound_chording(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x61, 1), commit)

    def disable_compound_chording(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x61, 0), commit)

    def set_compound_tolerance(
        self, value: int = 1500, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x64, value), commit)

    def set_operating_system(
        self, os: OperatingSystem, *, commit: bool = False
    ) -> bool:
        return self._maybe_commit(self.set_parameter(0x91, hex(os.value)), commit)

    def enable_realtime_feedback(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x92, 1), commit)

    def disable_realtime_feedback(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x92, 0), commit)

    def enable_startup_message(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x93, 1), commit)

    def disable_startup_message(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x93, 0), commit)

    def reset_parameters(self):
        self._execute("RST", "PARAMS")

    def get_keymap(self, keymap: Keymap, index: int) -> int:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")

        return int(self._execute("VAR", "B3", keymap.value, index)[0])

    def set_keymap(
        self, keymap: Keymap, index: int, action_id: int, *, commit: bool = False
    ) -> bool:
        if issubclass(self.__class__, CharaChorderOne) and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if issubclass(self.__class__, CharaChorderLite) and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")
        if action_id not in range(8, 2048):
            raise IndexError("Action id out of range. Must be between 8-2047")

        return self._maybe_commit(
            self._execute("VAR", "B4", keymap.value, index, action_id)[0] == "0", commit
        )

    def reset_keymaps(self):
        self._execute("RST", "KEYMAPS")

    def restart(self, *, reconnect_timeout: float = 10.0):
        try:
            self._execute("RST")
        except serialutil.SerialException:
            self._reconnect(timeout=reconnect_timeout)
        else:
            # This has been recorded in the CC1 M0
            raise RestartFailure

    def factory_reset(self):
        self._execute("RST", "FACTORY")

    def enter_bootloader_mode(self):
        self._execute("RST", "BOOTLOADER")

    def get_available_ram(self) -> int:
        return int(self._execute("RAM")[0])

    def sim(self, subcommand: str, value: str) -> str:
        return self._execute("SIM", subcommand, value)[0]


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

    def is_gui_ctrl_swapped(self) -> bool:
        return bool(self.get_parameter(0x13))

    def enable_gui_ctrl_swap(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x13, 1), commit)

    def disable_gui_ctrl_swap(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x13, 0), commit)

    def is_led_enabled(self) -> bool:
        return bool(self.get_parameter(0x84))

    def enable_led(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x84, 1), commit)

    def disable_led(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x84, 0), commit)

    def get_led_brightness(self) -> int:
        return self.get_parameter(0x81)

    def set_led_brightness(self, value: int = 5, *, commit: bool = False) -> bool:
        return bool(self._maybe_commit(self.set_parameter(0x81, value), commit))

    def get_led_color_code(self) -> int:
        return self.get_parameter(0x82)

    def set_led_color_code(self, value: int = 5, *, commit: bool = False) -> int:
        return self._maybe_commit(self.set_parameter(0x82, value), commit)

    def is_led_key_highlight_enabled(self) -> bool:
        return bool(self.get_parameter(0x83))

    def enable_led_key_highlight(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x83, 1), commit)

    def disable_led_key_highlight(self, *, commit: bool = False) -> bool:
        return self._maybe_commit(self.set_parameter(0x83, 0), commit)


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
