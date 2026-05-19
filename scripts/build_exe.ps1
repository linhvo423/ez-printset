$ErrorActionPreference = "Stop"

py -m pip install -r requirements.txt
py -m pip install pyinstaller
pyinstaller --clean --noconfirm EZ-PrintSet.spec

Write-Host "Build complete: dist\EZ-PrintSet.exe"
