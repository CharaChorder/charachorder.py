from typing import List


__all__ = [
    "CharaChorderException",
    "UnknownDevice",
    "SerialException",
    "UnknownCommand",
    "InvalidResponse",
]


class CharaChorderException(Exception):
    """Base exception class for charachorder"""


class UnknownDevice(CharaChorderException):
    """An exception raised when an unknown device was loaded as a CharaChorder device"""

    def __init__(self, device):
        super().__init__(f'Device "{device}" cannot be parsed as a CharaChorder device')


class SerialException(CharaChorderException):
    """An exception raised when something went wrong during Serial I/O"""


class UnknownCommand(SerialException):
    """An exception raised when an unknown command is passed to the Serial API"""

    def __init__(self, command: str):
        super().__init__(f'The command "{command}" does not exist')


class InvalidResponse(SerialException):
    """An exception raised when the response of a command was invalid"""

    def __init__(self, command: str, response: List[str]):
        super().__init__(
            f'The command "{command}" produced an invalid response: "{response}"'
        )
