from __future__ import annotations

__all__ = [
    "CharaChorderException",
    "UnknownProduct",
    "UnknownVendor",
    "SerialException",
    "UnknownCommand",
    "InvalidParameter",
    "InvalidParameterInput",
]


class CharaChorderException(Exception):
    """Base exception class for charachorder"""


class UnknownProduct(CharaChorderException):
    """An exception raised when the pid of the peripheral is foreign"""

    def __init__(self, id: int):
        super().__init__(
            f'Device with product id "{id}" cannot be parsed as a CharaChorder device'
        )


class UnknownVendor(CharaChorderException):
    """An exception raised when the vid of the peripheral is foreign"""

    def __init__(self, id: int):
        super().__init__(
            f'Device with vendor id "{id}" cannot be parsed as a CharaChorder device'
        )


class SerialException(CharaChorderException):
    """An exception raised when something went wrong during Serial I/O"""


class SerialConnectionNotFound(SerialException):
    def __init__(self) -> None:
        super().__init__(
            "Serial connection does not exist. Did you open the connection?"
        )


class UnknownCommand(SerialException):
    """An exception raised when an unknown command is passed to the Serial API"""

    def __init__(self, command: str):
        super().__init__(f'The command "{command}" does not exist')


class InvalidParameter(SerialException):
    """An exception raised when the given parameter code does not exist"""

    def __init__(self, code: str):
        super().__init__(f'The parameter "{code}" does not exist.')


class InvalidParameterInput(SerialException):
    """An exception raised when the given input for a parameter code is invalid"""

    def __init__(self, code: str, value: int | str):
        super().__init__(
            f'The parameter value "{value}" for the code "{code}" is invalid.'
        )
