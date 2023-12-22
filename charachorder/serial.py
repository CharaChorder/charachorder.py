from enum import Enum
from typing import Optional, Tuple, Union

from serial import Serial

from .device import CCDevice
from .errors import UnknownCommand


class Hexadecimal(str):
    def __init__(self, hexadecimal: str):
        try:
            int(hexadecimal, 16)
        except ValueError:
            raise ValueError("Value must be a hex string")


class KeymapCode(Enum):
    primary = 0xA1
    secondary = 0xA2
    tertiary = 0xA3


class ParameterCode(Enum):
    enable_serial_header = 0x01
    enable_serial_logging = 0x02
    enable_serial_debugging = 0x03
    enable_serial_raw = 0x04
    enable_serial_chord = 0x05
    enable_serial_keyboard = 0x06
    enable_serial_mouse = 0x07
    enable_usb_hid_keyboard = 0x11
    enable_character_entry = 0x12
    gui_ctrl_swap_mode = 0x13
    key_scan_duration = 0x14
    key_debounce_press_duration = 0x15
    key_debounce_release_duration = 0x16
    keyboard_output_character_microsecond_delays = 0x17
    enable_usb_hid_mouse = 0x21
    slow_mouse_speed = 0x22
    fast_mouse_speed = 0x23
    enable_active_mouse = 0x24
    mouse_scroll_speed = 0x25
    mouse_poll_duration = 0x26
    enable_chording = 0x31
    enable_chording_character_counter_timeout = 0x32
    chording_character_counter_timeout_timer = 0x33
    chord_detection_press_tolerance = 0x34
    chord_detection_release_tolerance = 0x35
    enable_spurring = 0x41
    enable_spurring_character_counter_timeout = 0x42
    spurring_character_counter_timeout_timer = 0x43
    enable_arpeggiates = 0x51
    arpeggiate_tolerance = 0x52
    enable_compound_chording_ = 0x61
    compound_tolerance = 0x64
    led_brightness = 0x81
    led_color_code = 0x82
    enable_led_key_highlight_ = 0x83
    enable_leds = 0x84
    operating_system = 0x91
    enable_realtime_feedback = 0x92
    enable_charachorder_ready_on_startup = 0x93


class CCSerial:
    def __init__(self, device: CCDevice):
        self.device = device

    def __enter__(self):
        self.connection = Serial(self.device.port, 115200, timeout=1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def execute(self, *args: Union[int, str]) -> Tuple[str, ...]:
        command = " ".join(map(str, args))
        self.connection.write(f"{command}\r\n".encode("utf-8"))
        output = tuple(self.connection.readline().decode("utf-8").strip().split(" "))

        command_from_output = output[: len(args)]
        actual_output = output[len(args) :]

        if command_from_output[0] == "UKN":
            raise UnknownCommand(command)

        return actual_output

    # ID
    def get_device_id(self) -> str:
        return " ".join(self.execute("ID"))

    # VERSION
    def get_device_version(self) -> str:
        return self.execute("VERSION")[0]

    # CML

    def get_chordmap_count(self) -> int:
        return int(self.execute("CML", "C0")[0])

    def get_chordmap_by_index(self, index: int) -> Tuple[Hexadecimal, Hexadecimal]:
        if index not in range(self.get_chordmap_count()):
            raise IndexError("Chordmap index out of range")

        chord, chordmap, success = self.execute("CML", "C1", index)
        return Hexadecimal(chord), Hexadecimal(chordmap)

    def get_chordmap_by_chord(self, chord: Hexadecimal) -> Optional[str]:
        chordmap = self.execute("CML", "C2", chord)[0]
        return chordmap if chordmap != "0" else None

    def set_chordmap_by_chord(self, chord: Hexadecimal, chordmap: Hexadecimal) -> bool:
        return self.execute("CML", "C3", chord, chordmap)[0] == "0"

    def del_chordmap_by_chord(self, chord: Hexadecimal) -> bool:
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
        if self.device.product == "One" and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if self.device.product == "Lite" and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")

        return int(self.execute("VAR", "B3", code.value, index)[0])

    def set_keymap(self, code: KeymapCode, index: int, action_id: int) -> bool:
        if self.device.product == "One" and index not in range(90):
            raise IndexError("Keymap index out of range. Must be between 0-89")
        if self.device.product == "Lite" and index not in range(67):
            raise IndexError("Keymap index out of range. Must be between 0-66")
        if action_id not in range(8, 2048):
            raise IndexError("Action id out of range. Must be between 8-2047")

        return self.execute("VAR", "B4", code.value, index, action_id)[0] == "0"

    # RST

    def restart_device(self):
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
    def sim(self, subcommand: str, value: Hexadecimal) -> Hexadecimal:
        return Hexadecimal(self.execute("SIM", subcommand, value)[0])
