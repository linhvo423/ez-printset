from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .models import LabelPreset, validate_label_size, validate_liner_width
from .paths import APP_ICON_PATH, DEFAULT_PRESETS_PATH, PRESETS_PATH
from .presets import load_presets, save_presets, upsert_preset
from .windows_printer import (
    PrinterBackendError,
    apply_label_preset,
    apply_stock,
    list_printer_stocks,
    list_printers,
)


class PrintSetApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EZ PrintSet")
        self._set_app_icon()
        self.geometry("760x540")
        self.minsize(720, 500)

        self.presets = load_presets(PRESETS_PATH) or load_presets(DEFAULT_PRESETS_PATH)
        self.printers = []
        self.stocks = []

        self.printer_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.stock_orientation_var = tk.StringVar(value="portrait")
        self.preset_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.liner_left_var = tk.StringVar(value="0")
        self.liner_right_var = tk.StringVar(value="0")
        self.custom_orientation_var = tk.StringVar(value="portrait")
        self.status_var = tk.StringVar(value="San sang.")

        self._build_ui()
        self._load_printers()
        self._refresh_presets()

    def _set_app_icon(self) -> None:
        if not APP_ICON_PATH.exists():
            return
        try:
            self.iconbitmap(str(APP_ICON_PATH))
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=18)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        ttk.Label(root, text="May in").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.printer_combo = ttk.Combobox(root, textvariable=self.printer_var, state="readonly")
        self.printer_combo.grid(row=0, column=1, sticky="ew", pady=(0, 10))
        self.printer_combo.bind("<<ComboboxSelected>>", self._on_printer_selected)
        ttk.Button(root, text="Tai lai", command=self._load_printers).grid(row=0, column=2, padx=(10, 0), pady=(0, 10))

        notebook = ttk.Notebook(root)
        notebook.grid(row=1, column=0, columnspan=3, sticky="nsew")

        stock_tab = ttk.Frame(notebook, padding=14)
        custom_tab = ttk.Frame(notebook, padding=14)
        stock_tab.columnconfigure(1, weight=1)
        custom_tab.columnconfigure(1, weight=1)
        notebook.add(stock_tab, text="Stock co san")
        notebook.add(custom_tab, text="Tao moi")

        self._build_stock_tab(stock_tab)
        self._build_custom_tab(custom_tab)

        status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 0))

    def _build_stock_tab(self, root: ttk.Frame) -> None:
        ttk.Label(root, text="Stock trong driver").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.stock_combo = ttk.Combobox(root, textvariable=self.stock_var, state="readonly")
        self.stock_combo.grid(row=0, column=1, sticky="ew", pady=(0, 10))
        self.stock_combo.bind("<<ComboboxSelected>>", self._on_stock_selected)
        ttk.Button(root, text="Tai stock", command=self._load_stocks).grid(row=0, column=2, padx=(10, 0), pady=(0, 10))

        ttk.Label(root, text="Chieu in").grid(row=1, column=0, sticky="w", pady=(0, 10))
        orientation_frame = ttk.Frame(root)
        orientation_frame.grid(row=1, column=1, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Radiobutton(orientation_frame, text="Doc", variable=self.stock_orientation_var, value="portrait").pack(side="left")
        ttk.Radiobutton(orientation_frame, text="Ngang", variable=self.stock_orientation_var, value="landscape").pack(side="left", padx=(18, 0))

        action_frame = ttk.Frame(root)
        action_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(18, 0))
        action_frame.columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Ap dung stock", command=self._apply_current_stock).grid(row=0, column=1)

    def _build_custom_tab(self, root: ttk.Frame) -> None:
        ttk.Label(root, text="Kich thuoc da luu").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.preset_combo = ttk.Combobox(root, textvariable=self.preset_var, state="readonly")
        self.preset_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 8))
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        ttk.Label(root, text="Ten stock moi").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.name_var).grid(row=1, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Rong tem (mm)").grid(row=2, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.width_var).grid(row=2, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Cao tem (mm)").grid(row=3, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.height_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Liner trai/phai (mm)").grid(row=4, column=0, sticky="w", pady=(0, 8))
        liner_frame = ttk.Frame(root)
        liner_frame.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(0, 8))
        liner_frame.columnconfigure(0, weight=1)
        liner_frame.columnconfigure(1, weight=1)
        ttk.Entry(liner_frame, textvariable=self.liner_left_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Entry(liner_frame, textvariable=self.liner_right_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(root, text="Chieu in").grid(row=5, column=0, sticky="w", pady=(0, 8))
        orientation_frame = ttk.Frame(root)
        orientation_frame.grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Radiobutton(orientation_frame, text="Doc", variable=self.custom_orientation_var, value="portrait").pack(side="left")
        ttk.Radiobutton(orientation_frame, text="Ngang", variable=self.custom_orientation_var, value="landscape").pack(side="left", padx=(18, 0))

        action_frame = ttk.Frame(root)
        action_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        action_frame.columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Luu kich thuoc", command=self._save_current_preset).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(action_frame, text="Tao va ap dung", command=self._apply_current_preset).grid(row=0, column=2)

    def _load_printers(self) -> None:
        try:
            self.printers = list_printers()
        except PrinterBackendError as exc:
            self.status_var.set(str(exc))
            self.printer_combo["values"] = []
            return

        names = [printer.name for printer in self.printers]
        self.printer_combo["values"] = names
        if names and not self.printer_var.get():
            self.printer_var.set(names[0])
        self.status_var.set(f"Tim thay {len(names)} may in.")
        self._load_stocks()

    def _on_printer_selected(self, _event=None) -> None:
        self._load_stocks()

    def _load_stocks(self) -> None:
        printer_name = self.printer_var.get()
        self.stocks = []
        self.stock_var.set("")
        self.stock_combo["values"] = []
        if not printer_name:
            return

        try:
            self.stocks = list_printer_stocks(printer_name)
        except PrinterBackendError as exc:
            self.status_var.set(str(exc))
            return

        values = [self._stock_label(stock) for stock in self.stocks]
        self.stock_combo["values"] = values
        if values:
            self.stock_combo.current(0)
        self.status_var.set(f"Doc duoc {len(values)} stock tu {printer_name}.")

    def _on_stock_selected(self, _event=None) -> None:
        stock = self._selected_stock()
        if stock:
            self.status_var.set(f"Da chon stock {stock.name}.")

    def _stock_label(self, stock) -> str:
        if stock.width_mm and stock.height_mm:
            return f"{stock.name} ({stock.width_mm:g} x {stock.height_mm:g} mm)"
        return stock.name

    def _selected_stock(self):
        index = self.stock_combo.current()
        if index < 0 or index >= len(self.stocks):
            return None
        return self.stocks[index]

    def _refresh_presets(self) -> None:
        names = [preset.name for preset in self.presets]
        self.preset_combo["values"] = names
        if names and not self.preset_var.get():
            self.preset_var.set(names[0])
            self._fill_form(self.presets[0])

    def _on_preset_selected(self, _event=None) -> None:
        preset = self._selected_preset()
        if preset:
            self._fill_form(preset)

    def _fill_form(self, preset: LabelPreset) -> None:
        self.name_var.set(preset.name)
        self.width_var.set(str(preset.width_mm).rstrip("0").rstrip("."))
        self.height_var.set(str(preset.height_mm).rstrip("0").rstrip("."))
        self.liner_left_var.set(str(preset.liner_left_mm).rstrip("0").rstrip(".") or "0")
        self.liner_right_var.set(str(preset.liner_right_mm).rstrip("0").rstrip(".") or "0")
        self.custom_orientation_var.set(preset.orientation)

    def _current_preset(self) -> LabelPreset:
        try:
            width_mm = float(self.width_var.get().replace(",", "."))
            height_mm = float(self.height_var.get().replace(",", "."))
            liner_left_mm = float(self.liner_left_var.get().replace(",", ".") or 0)
            liner_right_mm = float(self.liner_right_var.get().replace(",", ".") or 0)
        except ValueError as exc:
            raise ValueError("Rong, cao va liner phai la so.") from exc

        validate_label_size(width_mm, height_mm)
        validate_liner_width(liner_left_mm, liner_right_mm)
        name = self.name_var.get().strip() or f"Tem {width_mm:g} x {height_mm:g} mm"
        return LabelPreset(
            name=name,
            width_mm=width_mm,
            height_mm=height_mm,
            orientation=self.custom_orientation_var.get(),
            liner_left_mm=liner_left_mm,
            liner_right_mm=liner_right_mm,
        )

    def _selected_preset(self) -> LabelPreset | None:
        name = self.preset_var.get()
        for preset in self.presets:
            if preset.name == name:
                return preset
        return None

    def _save_current_preset(self) -> None:
        try:
            preset = self._current_preset()
        except ValueError as exc:
            messagebox.showerror("Du lieu chua hop le", str(exc))
            return

        self.presets = upsert_preset(self.presets, preset)
        save_presets(PRESETS_PATH, self.presets)
        self.preset_var.set(preset.name)
        self._refresh_presets()
        self.status_var.set(f"Da luu kich thuoc {preset.name}.")

    def _apply_current_stock(self) -> None:
        printer_name = self.printer_var.get()
        stock = self._selected_stock()
        if not printer_name:
            messagebox.showerror("Chua chon may in", "Hay chon may in truoc khi ap dung.")
            return
        if not stock:
            messagebox.showerror("Chua chon stock", "Hay chon stock co san truoc khi ap dung.")
            return

        self.status_var.set("Dang ap dung stock...")
        self._set_buttons_state("disabled")
        thread = threading.Thread(
            target=self._apply_stock_worker,
            args=(printer_name, stock, self.stock_orientation_var.get()),
            daemon=True,
        )
        thread.start()

    def _apply_current_preset(self) -> None:
        printer_name = self.printer_var.get()
        if not printer_name:
            messagebox.showerror("Chua chon may in", "Hay chon may in truoc khi ap dung.")
            return

        try:
            preset = self._current_preset()
        except ValueError as exc:
            messagebox.showerror("Du lieu chua hop le", str(exc))
            return

        self.status_var.set("Dang tao va ap dung stock moi...")
        self._set_buttons_state("disabled")
        thread = threading.Thread(target=self._apply_preset_worker, args=(printer_name, preset), daemon=True)
        thread.start()

    def _apply_stock_worker(self, printer_name: str, stock, orientation: str) -> None:
        try:
            result = apply_stock(printer_name, stock, orientation)
        except Exception as exc:
            self.after(0, self._apply_failed, exc)
            return
        self.after(0, self._stock_apply_done, printer_name, stock, result)

    def _apply_preset_worker(self, printer_name: str, preset: LabelPreset) -> None:
        try:
            result = apply_label_preset(printer_name, preset)
        except Exception as exc:
            self.after(0, self._apply_failed, exc)
            return
        self.after(0, self._preset_apply_done, printer_name, preset, result)

    def _stock_apply_done(self, printer_name: str, stock, result) -> None:
        self._set_buttons_state("normal")
        message = f"Da ap dung stock {stock.name} cho {printer_name}."
        self._show_apply_result(message, result)

    def _preset_apply_done(self, printer_name: str, preset: LabelPreset, result) -> None:
        self._set_buttons_state("normal")
        message = f"Da tao va ap dung {preset.width_mm:g} x {preset.height_mm:g} mm cho {printer_name}."
        if preset.liner_left_mm or preset.liner_right_mm:
            message += f" Liner: {preset.liner_left_mm:g}/{preset.liner_right_mm:g} mm."
        self._show_apply_result(message, result)

    def _show_apply_result(self, message: str, result) -> None:
        if result.scope == "user":
            message += " Da luu cho user hien tai."
        self.status_var.set(message)
        if result.warnings:
            messagebox.showwarning("Da ap dung voi canh bao", message + "\n\n" + "\n".join(result.warnings))
        else:
            messagebox.showinfo("Thanh cong", message)

    def _apply_failed(self, exc: Exception) -> None:
        self._set_buttons_state("normal")
        self.status_var.set(str(exc))
        messagebox.showerror("Khong ap dung duoc", str(exc))

    def _set_buttons_state(self, state: str) -> None:
        for child in self.winfo_children():
            self._set_state_recursive(child, state)

    def _set_state_recursive(self, widget: tk.Widget, state: str) -> None:
        try:
            if isinstance(widget, ttk.Button):
                widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, state)


def run_gui() -> int:
    app = PrintSetApp()
    app.mainloop()
    return 0
