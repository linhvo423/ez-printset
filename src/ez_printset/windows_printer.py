from __future__ import annotations

import platform
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from .models import LabelPreset, validate_label_size, validate_liner_width


class PrinterBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class PrinterInfo:
    name: str
    driver_name: str = ""
    port_name: str = ""


@dataclass(frozen=True)
class StockInfo:
    name: str
    paper_id: int | None = None
    width_mm: float | None = None
    height_mm: float | None = None


@dataclass(frozen=True)
class ApplyResult:
    scope: str
    warnings: tuple[str, ...] = ()


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


def apply_label_preset(printer_name: str, preset: LabelPreset) -> ApplyResult:
    require_windows_backend()
    validate_label_size(preset.width_mm, preset.height_mm)
    validate_liner_width(preset.liner_left_mm, preset.liner_right_mm)
    validate_label_size(preset.effective_width_mm, preset.height_mm)
    warnings = []
    try:
        ensure_form(printer_name, preset)
    except PrinterBackendError as exc:
        warnings.append(str(exc))
    result = _apply_devmode(printer_name, preset)
    if warnings:
        return ApplyResult(scope=result.scope, warnings=tuple([*warnings, *result.warnings]))
    return result


def apply_stock(printer_name: str, stock: StockInfo, orientation: str = "portrait") -> ApplyResult:
    require_windows_backend()
    paper_id = stock.paper_id or _find_driver_paper_id(
        printer_name,
        _get_printer_port_name(printer_name),
        stock.name,
    )
    return _apply_devmode_values(
        printer_name=printer_name,
        form_name=stock.name,
        paper_id=paper_id,
        width_mm=stock.width_mm,
        height_mm=stock.height_mm,
        orientation=orientation,
    )


def list_printer_stocks(printer_name: str) -> list[StockInfo]:
    require_windows_backend()
    import win32con
    import win32print

    port_name = _get_printer_port_name(printer_name)
    if not port_name:
        return []

    try:
        paper_names = win32print.DeviceCapabilities(printer_name, port_name, win32con.DC_PAPERNAMES)
        paper_ids = win32print.DeviceCapabilities(printer_name, port_name, win32con.DC_PAPERS)
        paper_sizes = win32print.DeviceCapabilities(printer_name, port_name, win32con.DC_PAPERSIZE)
    except Exception as exc:
        raise PrinterBackendError("Khong doc duoc danh sach stock tu driver may in.") from exc

    stocks: list[StockInfo] = []
    for index, raw_name in enumerate(paper_names):
        name = _clean_driver_name(raw_name)
        if not name:
            continue

        paper_id = int(paper_ids[index]) if index < len(paper_ids) else None
        width_mm = None
        height_mm = None
        if index < len(paper_sizes):
            width_mm, height_mm = _paper_size_to_mm(paper_sizes[index])

        stocks.append(
            StockInfo(
                name=name,
                paper_id=paper_id,
                width_mm=width_mm,
                height_mm=height_mm,
            )
        )

    return stocks


def ensure_form(printer_name: str, preset: LabelPreset) -> None:
    require_windows_backend()
    import pywintypes
    import win32print

    size = _form_size(preset.effective_width_mm, preset.height_mm)
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

    with open_printer_for_write(printer_name) as printer:
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
                f"Khong tao duoc paper size '{preset.form_name}'. App se thu ap dung bang custom size truc tiep."
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


@contextmanager
def open_printer_for_write(printer_name: str) -> Iterator[object]:
    import pywintypes
    import win32print

    try:
        all_access = getattr(win32print, "PRINTER_ALL_ACCESS", None)
        if all_access is None:
            printer = win32print.OpenPrinter(printer_name)
        else:
            printer = win32print.OpenPrinter(printer_name, {"DesiredAccess": all_access})
    except pywintypes.error:
        printer = win32print.OpenPrinter(printer_name)

    try:
        yield printer
    finally:
        win32print.ClosePrinter(printer)


def _apply_devmode(printer_name: str, preset: LabelPreset) -> ApplyResult:
    paper_id = _find_driver_paper_id(
        printer_name,
        _get_printer_port_name(printer_name),
        preset.form_name,
    )
    return _apply_devmode_values(
        printer_name=printer_name,
        form_name=preset.form_name,
        paper_id=paper_id,
        width_mm=preset.effective_width_mm,
        height_mm=preset.height_mm,
        orientation=preset.orientation,
    )


def _apply_devmode_values(
    printer_name: str,
    form_name: str,
    paper_id: int | None,
    width_mm: float | None,
    height_mm: float | None,
    orientation: str,
) -> ApplyResult:
    import pywintypes
    import win32con
    import win32print

    with open_printer_for_write(printer_name) as printer:
        info = win32print.GetPrinter(printer, 2)
        devmode = info.get("pDevMode")
        if devmode is None:
            raise PrinterBackendError("Driver khong tra ve cau hinh DEVMODE.")

        devmode.FormName = form_name
        devmode.PaperSize = paper_id or getattr(win32con, "DMPAPER_USER", 256)
        devmode.Orientation = (
            win32con.DMORIENT_LANDSCAPE
            if orientation == "landscape"
            else win32con.DMORIENT_PORTRAIT
        )
        devmode.Fields |= win32con.DM_FORMNAME | win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION
        if width_mm:
            devmode.PaperWidth = _devmode_size(width_mm)
            devmode.Fields |= win32con.DM_PAPERWIDTH
        if height_mm:
            devmode.PaperLength = _devmode_size(height_mm)
            devmode.Fields |= win32con.DM_PAPERLENGTH

        flags = win32con.DM_IN_BUFFER | win32con.DM_OUT_BUFFER
        validated = win32print.DocumentProperties(0, printer, printer_name, devmode, devmode, flags)
        if hasattr(validated, "Fields"):
            info["pDevMode"] = validated
        else:
            info["pDevMode"] = devmode

        try:
            win32print.SetPrinter(printer, 2, info, 0)
            return ApplyResult(scope="printer")
        except pywintypes.error:
            try:
                win32print.SetPrinter(printer, 9, {"pDevMode": info["pDevMode"]}, 0)
                return ApplyResult(
                    scope="user",
                    warnings=("Windows/driver khong cho ghi mac dinh may in, da ap dung cho user hien tai.",),
                )
            except pywintypes.error as user_exc:
                raise PrinterBackendError(
                    "Khong ap dung duoc cau hinh. Hay kiem tra printer driver hoac thu dong/mo lai Printing Preferences."
                ) from user_exc


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
        if _clean_driver_name(name).lower() == target:
            return int(paper_id)
    return None


def _get_printer_port_name(printer_name: str) -> str:
    import win32print

    with open_printer(printer_name) as printer:
        info = win32print.GetPrinter(printer, 2)
    return str(info.get("pPortName") or "")


def _clean_driver_name(value: object) -> str:
    return str(value).replace("\x00", "").strip()


def _paper_size_to_mm(value: object) -> tuple[float | None, float | None]:
    try:
        width = getattr(value, "x", None)
        height = getattr(value, "y", None)
        if width is None or height is None:
            width, height = value
        return round(float(width) / 10, 2), round(float(height) / 10, 2)
    except Exception:
        return None, None
