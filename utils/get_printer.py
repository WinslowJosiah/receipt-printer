import os

# HACK To add software columns to the ESC/POS printer classes, this must
# come before every other import from escpos.
import escpos
from printer.escpos_with_software_columns import EscposWithSoftwareColumns
escpos.escpos.Escpos = EscposWithSoftwareColumns

from escpos.printer import File
from escpos.exceptions import DeviceNotFoundError

from printer import Bluetooth


def get_file_printer(filename: str):
    filename, _ = os.path.splitext(os.path.basename(filename))
    printer = File(f"{filename}.bin", profile="ZJ-5870")
    printer.open()
    return printer


def get_printer(filename: str, file: bool = False):
    if file:
        print("Printing to file")
        return get_file_printer(filename)

    if not Bluetooth.is_usable():
        print("Bluetooth not usable; printing to file")
        return get_file_printer(filename)

    try:
        printer = Bluetooth("86:67:7a:b0:fb:5b", port=1, profile="ZJ-5870")
        printer.open()
        print("Printing to Bluetooth printer")
    except (DeviceNotFoundError, RuntimeError):
        try:
            printer.close()
        except RuntimeError:
            pass
        printer = get_file_printer(filename)
        print("Bluetooth printer not found; printing to file")

    return printer
