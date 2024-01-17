from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class Chord(tuple):
    def to_hex(self) -> str:
        hexadecimal = 0
        for i in range(1, len(self) + 1):
            hexadecimal |= (ord(self[-i]) & 0x3FF) << (12 - i) * 10
        return format(hexadecimal, "032X")

    @classmethod
    def from_hex(cls, hexadecimal: int | str) -> Self:
        if isinstance(hexadecimal, int):
            chord = hexadecimal
        elif isinstance(hexadecimal, str):
            chord = int(hexadecimal, 16)

        actions = []
        for _ in range(12):
            action_code = int(chord & 0x3FF)
            if action_code != 0:
                actions.append(chr(action_code))
            chord >>= 10

        return cls(actions)


class ChordPhrase(tuple):
    def to_hex(self) -> str:
        def compress_phrase(phrase):
            buffer = bytearray(len(phrase) * 2)
            i = 0
            for char in phrase:
                action = ord(char)
                if action > 0xFF:
                    buffer[i] = action >> 8
                    i += 1
                buffer[i] = action & 0xFF
                i += 1
            return buffer[:i]

        compressed_actions = compress_phrase(self)
        return "".join(format(action, "02X") for action in compressed_actions)

    @classmethod
    def from_hex(cls, hexadecimal: str) -> Self:
        numeric_action_codes = []
        for i in range(0, len(hexadecimal), 2):
            numeric_action_codes.append(int(hexadecimal[i : i + 2], 16))

        action_codes = []
        for i, action_code in enumerate(numeric_action_codes):
            if action_code in range(32):  # 10-bit scan code
                action_codes[i + 1] = (action_code << 8) | action_codes[i + 1]

            elif action_code in range(32, 127):  # Alphanumeric
                action_codes.append(chr(action_code))

            elif action_code == 296:  # Line break
                action_codes.append("\n")

            elif action_code == 298 and len(action_codes) > 0:  # Backspace
                action_codes.pop()

            elif action_code == 299:  # Tab
                action_codes.append("\t")

            elif action_code == 544:  # Spaceright
                action_codes.append(" ")

            elif action_code > 126:  # Currently unsupported
                action_codes.append(f"<{action_code}>")

            else:
                action_codes.append(chr(action_code))
        return cls(action_codes)


class KeymapCode(Enum):
    primary = 0xA1
    secondary = 0xA2
    tertiary = 0xA3


class OperatingSystem(Enum):
    Windows = 0x0
    MacOS = 0x1
    Linux = 0x2
    iOS = 0x3
    Android = 0x4
    Unknown = 0x255
