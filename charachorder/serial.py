from typing import Optional, Tuple

from serial import Serial

from .device import CCDevice
from .errors import InvalidResponse, UnknownCommand


class Hexadecimal(str):
    def __init__(self, hexadecimal: str):
        try:
            int(hexadecimal, 16)
        except ValueError:
            raise ValueError("Value must be a hex string")


class CCSerial:
    def __init__(self, device: CCDevice):
        self.device = device

    def __enter__(self):
        self.connection = Serial(self.device.port, 115200, timeout=1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def execute(self, *args: str) -> Tuple[str, ...]:
        command = " ".join(args)
        self.connection.write(f"{command}\r\n".encode("utf-8"))
        output = tuple(self.connection.readline().decode("utf-8").strip().split(" "))

        command_from_output = output[: len(args)]
        actual_output = output[len(args) :]

        if command_from_output[0] == "UKN":
            raise UnknownCommand(command)
        if command_from_output != args:
            raise InvalidResponse(command, " ".join(output))

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

        chord, chordmap, success = self.execute("CML", "C1", str(index))
        if chord == "0" or chordmap == "0":
            raise InvalidResponse("CML C1", " ".join((chord, chordmap)))

        return Hexadecimal(chord), Hexadecimal(chordmap)

    def get_chordmap_by_chord(self, chord: Hexadecimal) -> Optional[str]:
        chordmap = self.execute("CML", "C2", chord)[0]
        return chordmap if chordmap != "0" else None

    def set_chordmap_by_chord(self, chord: Hexadecimal, chordmap: Hexadecimal) -> bool:
        return self.execute("CML", "C3", chord, chordmap)[0] == "0"

    def del_chordmap_by_chord(self, chord: Hexadecimal) -> bool:
        return self.execute("CML", "C4", chord)[0] == "0"
