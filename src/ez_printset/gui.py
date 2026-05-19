from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .models import LabelPreset, validate_label_size
from .paths import DEFAULT_PRESETS_PATH, PRESETS_PATH
from .presets import load_presets, save_presets, upsert_preset
from .windows_printer import PrinterBackendError, apply_label_preset, list_printers


class PrintSetApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EZ PrintSet")
        self.geometry("720x430")
        self.minsize(680, 390)

        self.presets = load_presets(PRESETS_PATH) or load_presets(DEFAULT_PRESETS_PATH)
        self.printers = []

        self.printer_var = tk.StringVar()
        self.preset_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.orientation_var = tk.StringVar(value="portrait")
        self.status_var = tk.StringVar(value="San sang.")

        self._build_ui()
        self._load_printers()
        self._refresh_presets()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=18)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="May in").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.printer_combo = ttk.Combobox(root, textvariable=self.printer_var, state="readonly")
        self.printer_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))
        ttk.Button(root, text="Tai lai", command=self._load_printers).grid(row=0, column=2, padx=(10, 0), pady=(0, 8))

        ttk.Label(root, text="Kich thuoc co san").grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.preset_combo = ttk.Combobox(root, textvariable=self.preset_var, state="readonly")
        self.preset_combo.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        separator = ttk.Separator(root)
        separator.grid(row=2, column=0, columnspan=3, sticky="ew", pady=12)

        ttk.Label(root, text="Ten kich thuoc").grid(row=3, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.name_var).grid(row=3, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Rong (mm)").grid(row=4, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.width_var).grid(row=4, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Cao (mm)").grid(row=5, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(root, textvariable=self.height_var).grid(row=5, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(root, text="Chieu in").grid(row=6, column=0, sticky="w", pady=(0, 8))
        orientation_frame = ttk.Frame(root)
        orientation_frame.grid(row=6, column=1, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Radiobutton(
            orientation_frame,
            text="Doc",
            variable=self.orientation_var,
            value="portrait",
        ).pack(side="left")
        ttk.Radiobutton(
            orientation_frame,
            text="Ngang",
            variable=self.orientation_var,
            value="landscape",
        ).pack(side="left", padx=(18, 0))

        action_frame = ttk.Frame(root)
        action_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        action_frame.columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Luu kich thuoc", command=self._save_current_preset).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(action_frame, text="Ap dung", command=self._apply_current_preset).grid(row=0, column=2)

        status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        status.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(18, 0))

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
        self.orientation_var.set(preset.orientation)

    def _current_preset(self) -> LabelPreset:
        try:
            width_mm = float(self.width_var.get().replace(",", "."))
            height_mm = float(self.height_var.get().replace(",", "."))
        except ValueError as exc:
            raise ValueError("Rong va cao phai la so.") from exc

        validate_label_size(width_mm, height_mm)
        name = self.name_var.get().strip() or f"Tem {width_mm:g} x {height_mm:g} mm"
        orientation = self.orientation_var.get()
        return LabelPreset(name=name, width_mm=width_mm, height_mm=height_mm, orientation=orientation)

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

        self.status_var.set("Dang ap dung cau hinh...")
        self._set_buttons_state("disabled")
        thread = threading.Thread(target=self._apply_worker, args=(printer_name, preset), daemon=True)
        thread.start()

    def _apply_worker(self, printer_name: str, preset: LabelPreset) -> None:
        try:
            apply_label_preset(printer_name, preset)
        except Exception as exc:
            self.after(0, self._apply_failed, exc)
            return
        self.after(0, self._apply_done, printer_name, preset)

    def _apply_done(self, printer_name: str, preset: LabelPreset) -> None:
        self._set_buttons_state("normal")
        message = f"Da ap dung {preset.width_mm:g} x {preset.height_mm:g} mm cho {printer_name}."
        self.status_var.set(message)
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
