from __future__ import annotations

import platform
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from .models import LabelPreset, validate_label_size


class PrinterBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class PrinterInfo:
    name: str
    driver_name: str = ""
    port_name: str = ""


def require_windows_backend():
    if platform.system() != "Windows":
        raise PrinterBackendError("Cong cu cau hinh may in chi chay tren Windows.")

    try:
        import pywintypes  # noqa: F401
        import win32con  # noqa: F401
        import win32print  # noqa: F401
    except ImportError as exc:
        raise PrinterBackendError(
            "Thieu thu vien pywin32. Hay cai bang lenh: py -m pip install -r requirements.txt"
        ) from exc


def list_printers() -> list[PrinterInfo]:
    require_windows_backend()
    import win32print

    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = []
    for item in win32print.EnumPrinters(flags, None, 2):
        printers.append(
            PrinterInfo(
                name=item.get("pPrinterName", ""),
                driver_name=item.get("pDriverName", ""),
                port_name=item.get("pPortName", ""),
            )
        )
    return sorted(printers, key=lambda printer: printer.name.lower())


def apply_label_preset(printer_name: str, preset: LabelPreset, scope: str = "machine") -> None:
    require_windows_backend()
    validate_label_size(preset.width_mm, preset.height_mm)
    ensure_form(printer_name, preset)
    _apply_devmode(printer_name, preset, scope)


def ensure_form(printer_name: str, preset: LabelPreset) -> None:
    require_windows_backend()
    import pywintypes
    import win32print

    size = _form_size(preset.width_mm, preset.height_mm)
    form = {
        "Flags": 0,
        "Name": preset.form_name,
        "Size": size,
        "ImageableArea": {
            "left": 0,
            "top": 0,
            "right": size["cx"],
            "bottom": size["cy"],
        },
    }

    with open_printer(printer_name) as printer:
        existing_names = {item["Name"].lower() for item in win32print.EnumForms(printer)}
        if preset.form_name.lower() in existing_names:
            try:
                win32print.SetForm(printer, preset.form_name, form)
            except pywintypes.error:
                # Some drivers do not allow updating a form currently in use.
                pass
            return

        try:
            win32print.AddForm(printer, form)
        except pywintypes.error as exc:
            raise PrinterBackendError(
                f"Khong tao duoc paper size '{preset.form_name}'. Hay chay app bang quyen Administrator "
                "hoac kiem tra driver co cho phep custom form khong."
            ) from exc


@contextmanager
def open_printer(printer_name: str, desired_access: int | None = None) -> Iterator[object]:
    import win32print

    defaults = None if desired_access is None else {"DesiredAccess": desired_access}
    printer = win32print.OpenPrinter(printer_name, defaults)
    try:
        yield printer
    finally:
        win32print.ClosePrinter(printer)


def _apply_devmode(printer_name: str, preset: LabelPreset, scope: str) -> None:
    import pywintypes
    import win32con
    import win32print

    with open_printer(printer_name) as printer:
        info = win32print.GetPrinter(printer, 2)
        devmode = info.get("pDevMode")
        if devmode is None:
            raise PrinterBackendError("Driver khong tra ve cau hinh DEVMODE.")

        paper_id = _find_driver_paper_id(printer_name, info.get("pPortName", ""), preset.form_name)
        devmode.FormName = preset.form_name
        devmode.PaperSize = paper_id or getattr(win32con, "DMPAPER_USER", 256)
        devmode.PaperWidth = _devmode_size(preset.width_mm)
        devmode.PaperLength = _devmode_size(preset.height_mm)
        devmode.Orientation = (
            win32con.DMORIENT_LANDSCAPE
            if preset.orientation == "landscape"
            else win32con.DMORIENT_PORTRAIT
        )
        devmode.Fields |= (
            win32con.DM_FORMNAME
            | win32con.DM_PAPERSIZE
            | win32con.DM_PAPERWIDTH
            | win32con.DM_PAPERLENGTH
            | win32con.DM_ORIENTATION
        )

        flags = win32con.DM_IN_BUFFER | win32con.DM_OUT_BUFFER
        validated = win32print.DocumentProperties(0, printer, printer_name, devmode, devmode, flags)
        if hasattr(validated, "Fields"):
            info["pDevMode"] = validated
        else:
            info["pDevMode"] = devmode

        if scope == "user":
            try:
                win32print.SetPrinter(printer, 9, {"pDevMode": info["pDevMode"]}, 0)
            except pywintypes.error as exc:
                raise PrinterBackendError(
                    "Khong ap dung duoc vao Printing Preferences cua user hien tai."
                ) from exc
            return

        try:
            win32print.SetPrinter(printer, 2, info, 0)
        except pywintypes.error as exc:
            raise PrinterBackendError(
                "Khong ap dung duoc vao mac dinh cua may in. Hay chay app bang quyen Administrator "
                "hoac bo chon 'Ap dung mac dinh may in'."
            ) from exc


def _form_size(width_mm: float, height_mm: float) -> dict[str, int]:
    return {"cx": int(round(width_mm * 1000)), "cy": int(round(height_mm * 1000))}


def _devmode_size(value_mm: float) -> int:
    return int(round(value_mm * 10))


def _find_driver_paper_id(printer_name: str, port_name: str, form_name: str) -> int | None:
    import win32con
    import win32print

    if not port_name:
        return None

    try:
        paper_names = win32print.DeviceCapabilities(printer_name, port_name, win32con.DC_PAPERNAMES)
        paper_ids = win32print.DeviceCapabilities(printer_name, port_name, win32con.DC_PAPERS)
    except Exception:
        return None

    target = form_name.strip().lower()
    for name, paper_id in zip(paper_names, paper_ids):
        if str(name).strip().lower() == target:
            return int(paper_id)
    return None
