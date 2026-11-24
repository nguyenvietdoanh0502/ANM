$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    throw 'Chua co .venv. Xem huong dan cai dat trong README.md.'
}
& '.\.venv\Scripts\python.exe' -m streamlit run app.py
