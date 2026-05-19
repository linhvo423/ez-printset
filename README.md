# EZ PrintSet

EZ PrintSet is a small Windows desktop tool for quickly creating and applying label paper sizes to a selected printer. It is intended for staff who need to switch label sizes without opening Windows Printing Preferences manually.

The app uses:

- `tkinter` for the desktop UI.
- `pywin32` for Windows printer APIs.
- Windows Forms plus printer `DEVMODE` to apply page setup defaults.

## Features

- List installed Windows printers.
- Read and apply driver-exposed stocks from the selected printer.
- Create reusable label size presets in millimeters.
- Add a Windows custom paper form when needed.
- Apply the selected paper size, orientation, width, and height to the printer default settings.
- Save presets to `profiles/presets.json`.

## Requirements

- Windows 10/11.
- Python 3.10 or newer.
- Seagull printer driver or another driver that supports Windows custom forms.

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run the app:

```powershell
py main.py
```

The desktop app has two separate flows:

- **Stock co san**: choose a stock already available in the selected printer driver, then apply it.
- **Tao moi**: enter a new label size, optional liner compensation, save it as a preset if needed, then create and apply it.

Run CLI commands:

```powershell
py main.py list
py main.py stocks --printer "Your Printer Name"
py main.py apply --printer "Your Printer Name" --width-mm 100 --height-mm 150
py main.py apply --printer "Your Printer Name" --width-mm 50 --height-mm 30 --landscape
py main.py apply --printer "Your Printer Name" --width-mm 100 --height-mm 150 --liner-left-mm 1.3 --liner-right-mm 1.3
```

## Build EXE

Install PyInstaller:

```powershell
py -m pip install pyinstaller
```

Build:

```powershell
pyinstaller --clean --noconfirm EZ-PrintSet.spec
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

The executable will be created in `dist/EZ-PrintSet.exe`.

## Set App Logo

Create or export a Windows icon file:

```txt
assets/app.ico
```

Recommended `.ico` sizes: `16x16`, `32x32`, `48x48`, and `256x256`.

After adding or replacing the icon, rebuild the app. GitHub Actions and `scripts/build_exe.ps1` will automatically use `assets/app.ico` as the executable icon and app window icon.

Create a release ZIP:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package_release.ps1
```

The ZIP will be created at `release/EZ-PrintSet-windows.zip`.

## Build With GitHub Actions

This repository includes `.github/workflows/build-windows.yml`.

After pushing the project to GitHub:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Build Windows EXE**.
4. Click **Run workflow**.
5. Open the completed workflow run.
6. Download the artifact named `EZ-PrintSet-windows`.

After extracting the downloaded artifact once, open the `EZ-PrintSet-windows` folder. It contains `EZ-PrintSet.exe` and `README.md`.

## Notes

Some Seagull driver options such as darkness, speed, sensor type, gap, and black mark may be stored in the driver's private `DEVMODE` area. This MVP focuses on paper size and orientation. Those advanced settings can be added later through driver profile export/import.

Creating a brand-new Windows custom form can require Administrator permission depending on Windows policy and the printer driver.

The app applies settings to the selected printer default. Run the app as Administrator if Windows blocks saving printer defaults.

The app can read driver-exposed stock names with `py main.py stocks --printer "Your Printer Name"` and from the **Stock trong driver** dropdown. If a Seagull stock exists only in the driver's private configuration and is not returned by Windows `DeviceCapabilities`, the next step is a Seagull stock/profile import flow.

For Seagull drivers that subtract **Exposed Liner Widths** from the displayed stock width, use the app's **Liner trai/phai (mm)** fields. They default to `0` and `0`. Example: if the driver has left/right liner `1.3 mm`, enter `1.3` and `1.3`; the app sends `label width + left liner + right liner` to compensate.
