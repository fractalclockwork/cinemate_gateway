# CircuitPython boot hooks.
# Capture-only builds disable USB HID so IR dumps cannot inject into the host.
# Map builds keep HID unless /CAPTURE_ONLY is present (host unique listen).
#
# Autoreload is OFF: host remounts / .Trash / indexer touches on CIRCUITPY were
# stopping code.py mid-run ("Code stopped by auto-reload") so IR LED went dead.
# Deploy always MCU-resets explicitly after copy.

CAPTURE_BUILD = False  # keep in sync with code.py MODE == "capture"

try:
    import supervisor

    supervisor.runtime.autoreload = False
except Exception:
    pass

try:
    import usb_hid

    disable = CAPTURE_BUILD
    if not disable:
        try:
            open("/CAPTURE_ONLY", "r").close()
            disable = True
        except OSError:
            pass
    if disable:
        usb_hid.disable()
except ImportError:
    pass
