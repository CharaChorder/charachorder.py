from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass
class Chord:
    raw: str

    def __str__(self) -> str:
        chord = int(self.raw, 16)

        actions = []
        for _ in range(12):
            action = int(chord & 0x3FF)
            if action != 0:
                actions.append(chr(action))
            chord >>= 10

        return "".join(actions)

    @classmethod
    def to_raw(cls, chord: str) -> Self:
        raw = 0
        for i in range(1, len(chord) + 1):
            raw |= (ord(chord[-i]) & 0x3FF) << (12 - i) * 10
        return cls(format(raw, "032X"))


@dataclass
class ChordPhrase:
    raw: str

    def __str__(self) -> str:
        numeric_action_codes = []
        for i in range(0, len(self.raw), 2):
            numeric_action_codes.append(int(self.raw[i : i + 2], 16))

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
        return "".join(action_codes)

    @classmethod
    def to_raw(cls, phrase: str) -> Self:
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

        compressed_actions = compress_phrase(phrase)
        return cls("".join(format(action, "02X") for action in compressed_actions))


class KeymapCode(Enum):
    primary = 0xA1
    secondary = 0xA2
    tertiary = 0xA3
