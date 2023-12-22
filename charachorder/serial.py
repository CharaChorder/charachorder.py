from typing import Tuple

from serial import Serial

from .device import CCDevice
from .errors import InvalidResponse, UnknownCommand


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
        output = self.connection.readline().decode("utf-8").strip().split(" ")

        command_from_output = tuple(output[: len(args)])
        actual_output = tuple(output[len(args) :])

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
