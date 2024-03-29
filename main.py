import threading
import time
from ctypes import windll, byref, Structure, WinError, POINTER, WINFUNCTYPE
from ctypes.wintypes import BOOL, HMONITOR, HDC, RECT, LPARAM, DWORD, BYTE, WCHAR, HANDLE

import pywinusb.hid as hid
from PIL import Image
from pystray import Icon, Menu, MenuItem

# Codes for different monitor inputs (REF: https://github.com/dot-osk/monitor_ctrl/blob/master/vcp_code.py)
# For more details, which I didn't use... (https://glenwing.github.io/docs/VESA-EDDC-1.2.pdf)
INPUT_CODES = {
    "DP1": 0x0F,
    "DP2": 0x10,
    "HDMI1": 0x11,
    "HDMI2": 0x12
}

# Which monitor input to use when keyboard is connected/disconnected
PLUGGED_IN = "DP2"
UNPLUGGED = "DP1"
KEYBOARD_NAME = "Corsair K70R Gaming Keyboard"

_MONITORENUMPROC = WINFUNCTYPE(BOOL, HMONITOR, HDC, POINTER(RECT), LPARAM)


class _PHYSICAL_MONITOR(Structure):
    _fields_ = [('handle', HANDLE),
                ('description', WCHAR * 128)]


def _iter_physical_monitors(close_handles=True):
    """Iterates physical monitors.

    The handles are closed automatically whenever the iterator is advanced.
    This means that the iterator should always be fully exhausted!

    If you want to keep handles e.g. because you need to store all of them and
    use them later, set `close_handles` to False and close them manually."""

    def callback(hmonitor, hdc, lprect, lparam):
        monitors.append(HMONITOR(hmonitor))
        return True

    monitors = []
    if not windll.user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(callback), None):
        raise WinError('EnumDisplayMonitors failed')

    for monitor in monitors:
        # Get physical monitor count
        count = DWORD()
        if not windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(monitor, byref(count)):
            raise WinError()
        # Get physical monitor handles
        physical_array = (_PHYSICAL_MONITOR * count.value)()
        if not windll.dxva2.GetPhysicalMonitorsFromHMONITOR(monitor, count.value, physical_array):
            raise WinError()
        for physical in physical_array:
            yield physical.handle
            if close_handles:
                if not windll.dxva2.DestroyPhysicalMonitor(physical.handle):
                    raise WinError()


def set_vcp_feature(monitor, code, value):
    """Sends a DDC command to the specified monitor.

    See this link for a list of commands:
    ftp://ftp.cis.nctu.edu.tw/pub/csie/Software/X11/private/VeSaSpEcS/VESA_Document_Center_Monitor_Interface/mccsV3.pdf
    """
    if not windll.dxva2.SetVCPFeature(HANDLE(monitor), BYTE(code), DWORD(value)):
        raise WinError()


def keyboard_connected():
    devices = hid.HidDeviceFilter().get_devices()
    try:
        for device in devices:
            if device.product_name == KEYBOARD_NAME:
                return True
    except Exception:
        return True

    return False


def set_input(input_str: str):
    if input_str in INPUT_CODES:
        for monitor in _iter_physical_monitors():
            set_vcp_feature(monitor, 0x60, INPUT_CODES[input_str])


def main():
    global paused, stopped

    keyboard_state = True

    while not stopped:
        if paused:
            time.sleep(0.1)
            continue

        connected = keyboard_connected()
        if keyboard_state != connected:
            try:
                if connected:
                    print(f"Keyboard connected, changing to {PLUGGED_IN}")
                    set_input(PLUGGED_IN)
                else:
                    print(f"Keyboard disconnected, changing to {UNPLUGGED}")
                    set_input(UNPLUGGED)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                keyboard_state = connected

        time.sleep(0.1)


def pause_swapper(icon, item):
    global paused
    paused = not item.checked
    print(f"Paused: {paused}")


def exit_program(icon, item):
    global stopped
    stopped = True
    icon.stop()


if __name__ == "__main__":
    paused = False
    stopped = False

    swapper = threading.Thread(target=main)
    swapper.daemon = True
    swapper.start()

    icon = Icon(
        'WindowSwapper',
        Image.open("icon.jpg"),
        menu=Menu(
            MenuItem('Paused', pause_swapper, checked=lambda item: paused),
            MenuItem('Exit', exit_program)
        )
    )

    icon.run()
