from __future__ import annotations

import argparse

from .gui import run_gui
from .models import LabelPreset
from .windows_printer import (
    PrinterBackendError,
    apply_label_preset,
    list_printer_stocks,
    list_printers,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZ PrintSet")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List installed printers")

    stocks_parser = subparsers.add_parser("stocks", help="List driver stocks for a printer")
    stocks_parser.add_argument("--printer", required=True)

    apply_parser = subparsers.add_parser("apply", help="Apply a label paper size to a printer")
    apply_parser.add_argument("--printer", required=True)
    apply_parser.add_argument("--width-mm", type=float, required=True)
    apply_parser.add_argument("--height-mm", type=float, required=True)
    apply_parser.add_argument("--name")
    apply_parser.add_argument("--landscape", action="store_true")
    apply_parser.add_argument("--liner-left-mm", type=float, default=0)
    apply_parser.add_argument("--liner-right-mm", type=float, default=0)

    args = parser.parse_args()

    if args.command == "list":
        return _list_printers()
    if args.command == "stocks":
        return _list_stocks(args)
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
        liner_left_mm=args.liner_left_mm,
        liner_right_mm=args.liner_right_mm,
    )

    try:
        result = apply_label_preset(args.printer, preset)
    except Exception as exc:
        print(exc)
        return 1

    print(f"Da ap dung {preset.width_mm:g} x {preset.height_mm:g} mm cho {args.printer}.")
    if result.scope == "user":
        print("Da luu cho user hien tai.")
    for warning in result.warnings:
        print(f"Canh bao: {warning}")
    return 0


def _list_stocks(args: argparse.Namespace) -> int:
    try:
        stocks = list_printer_stocks(args.printer)
    except PrinterBackendError as exc:
        print(exc)
        return 1

    for stock in stocks:
        size = ""
        if stock.width_mm and stock.height_mm:
            size = f" - {stock.width_mm:g} x {stock.height_mm:g} mm"
        paper_id = f" [paper_id={stock.paper_id}]" if stock.paper_id is not None else ""
        print(f"{stock.name}{size}{paper_id}")
    return 0

