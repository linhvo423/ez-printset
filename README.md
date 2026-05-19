# EZ PrintSet

EZ PrintSet is a small Windows desktop tool for quickly creating and applying label paper sizes to a selected printer. It is intended for staff who need to switch label sizes without opening Windows Printing Preferences manually.

The app uses:

- `tkinter` for the desktop UI.
- `pywin32` for Windows printer APIs.
- Windows Forms plus printer `DEVMODE` to apply page setup defaults.

## Features

- List installed Windows printers.
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

Run CLI commands:

```powershell
py main.py list
py main.py apply --printer "Your Printer Name" --width-mm 100 --height-mm 150
py main.py apply --printer "Your Printer Name" --width-mm 50 --height-mm 30 --landscape
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
6. Download the artifact named `EZ-PrintSet-windows` or `EZ-PrintSet-exe`.

The artifact `EZ-PrintSet-windows` contains `EZ-PrintSet-windows.zip`, which includes the Windows executable for staff.

## Notes

Some Seagull driver options such as darkness, speed, sensor type, gap, and black mark may be stored in the driver's private `DEVMODE` area. This MVP focuses on paper size and orientation. Those advanced settings can be added later through driver profile export/import.

Creating a brand-new Windows custom form can require Administrator permission depending on Windows policy and the printer driver. Applying an existing form to the current user's Printing Preferences is attempted first and usually does not require admin rights.
