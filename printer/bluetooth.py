import functools
import socket

# HACK To add software columns to the ESC/POS printer classes, this must
# come before every other import from escpos.
import escpos
from printer.escpos_with_software_columns import EscposWithSoftwareColumns
escpos.escpos.Escpos = EscposWithSoftwareColumns

from escpos.escpos import Escpos
from escpos.exceptions import DeviceNotFoundError


_DEP_BT = getattr(socket, "AF_BLUETOOTH", None) is not None


def is_usable() -> bool:
    return _DEP_BT


def dependency_bt(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_usable():
            raise RuntimeError(
                "Printing with Bluetooth connection requires Bluetooth "
                "support in the socket module."
            )
        return func(*args, **kwargs)
    return wrapper


class Bluetooth(Escpos):
    @staticmethod
    def is_usable() -> bool:
        return is_usable()

    def __init__(self, address: str = "", port: int = 1, *args, **kwargs):
        Escpos.__init__(self, *args, **kwargs)
        self.address = address
        self.port = port

        self._device = False

    @dependency_bt
    def open(self, raise_not_found: bool = True):
        if self._device:
            self.close()

        try:
            self.device = socket.socket(
                socket.AF_BLUETOOTH,
                socket.SOCK_STREAM,
                socket.BTPROTO_RFCOMM,
            )
            self.device.connect((self.address, self.port))
        except (OSError, TimeoutError) as e:
            self.device = None
            if raise_not_found:
                raise DeviceNotFoundError(
                    f"Unable to open Bluetooth printer on "
                    f"{(self.address, self.port)}:"
                    f"\n{e}"
                )
            else:
                return

    def _raw(self, msg: bytes):
        assert self.device
        self.device.send(msg)

    @dependency_bt
    def close(self):
        if not self._device:
            return
        self.device = False
