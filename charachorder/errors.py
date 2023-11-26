__all__ = [
    "CharaChorderException",
    "UnknownDevice",
]


class CharaChorderException(Exception):
    """Base exception class for charachorder"""


class UnknownDevice(CharaChorderException):
    """An exception raised when an unknown device was loaded as a CharaChorder device"""

    def __init__(self, device):
        super().__init__(f'Device "{device}" cannot be parsed as a CharaChorder device')
