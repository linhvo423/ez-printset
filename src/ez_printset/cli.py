from __future__ import annotations

import argparse

from .gui import run_gui
from .models import LabelPreset
from .windows_printer import PrinterBackendError, apply_label_preset, list_printers


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZ PrintSet")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List installed printers")

    apply_parser = subparsers.add_parser("apply", help="Apply a label paper size to a printer")
    apply_parser.add_argument("--printer", required=True)
    apply_parser.add_argument("--width-mm", type=float, required=True)
    apply_parser.add_argument("--height-mm", type=float, required=True)
    apply_parser.add_argument("--name")
    apply_parser.add_argument("--landscape", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        return _list_printers()
    if args.command == "apply":
        return _apply(args)
    return run_gui()


def _list_printers() -> int:
    try:
        printers = list_printers()
    except PrinterBackendError as exc:
        print(exc)
        return 1

    for printer in printers:
        details = " | ".join(filter(None, [printer.driver_name, printer.port_name]))
        print(f"{printer.name}" + (f" ({details})" if details else ""))
    return 0


def _apply(args: argparse.Namespace) -> int:
    preset = LabelPreset(
        name=args.name or f"Tem {args.width_mm:g} x {args.height_mm:g} mm",
        width_mm=args.width_mm,
        height_mm=args.height_mm,
        orientation="landscape" if args.landscape else "portrait",
    )

    try:
        apply_label_preset(args.printer, preset)
    except Exception as exc:
        print(exc)
        return 1

    print(f"Da ap dung {preset.width_mm:g} x {preset.height_mm:g} mm cho {args.printer}.")
    return 0
