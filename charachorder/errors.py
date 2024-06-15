from __future__ import annotations


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


class AutoReconnectFailure(SerialException):
    """An exception raised when auto-reconnect failed"""


class ReconnectTimeout(AutoReconnectFailure):
    """An exception raised when auto-reconnect failed due to a timeout"""

    def __init__(self) -> None:
        super().__init__(
            "An attempt to auto-reconnect has failed due to a timeout. You will need to re-create this object to do further Serial I/O"
        )


class TooManyDevices(AutoReconnectFailure):
    """An exception raised when auto-reconnect failed due to ambiguity in devices"""

    def __init__(self) -> None:
        super().__init__(
            "An attempt to auto-reconnect has failed due to two or more devices of the same model connected simultaneously which means the same device cannot be detected reliably. You will need to re-create this object to do further Serial I/O"
        )


class RestartFailure(SerialException):
    """An exception raised when restarting a device fails"""


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
        super().__init__(
            f'The parameter "{code}" does not exist. Note that all of the parameter commands have dedicated methods, please use those to avoid errors.'
        )


class InvalidParameterInput(SerialException):
    """An exception raised when the given input for a parameter code is invalid"""

    def __init__(self, code: str, value: int | str):
        super().__init__(
            f'The parameter value "{value}" for the code "{code}" is invalid. Note that all of the parameter commands have dedicated methods, please use those to avoid errors.'
        )
