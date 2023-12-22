__all__ = [
    "CharaChorderException",
    "UnknownProduct",
    "UnknownVendor",
    "SerialException",
    "UnknownCommand",
    "InvalidResponse",
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


class UnknownCommand(SerialException):
    """An exception raised when an unknown command is passed to the Serial API"""

    def __init__(self, command: str):
        super().__init__(f'The command "{command}" does not exist')


class InvalidResponse(SerialException):
    """An exception raised when the response of a command was invalid"""

    def __init__(self, command: str, response: str):
        super().__init__(
            f'The command "{command}" produced an invalid response: "{response}"'
        )
