@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if %ERRORLEVEL%==0 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
)
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
if /I "%1"=="setup" (
  python -m pip install --upgrade pip
  if exist "requirements.txt" (
    python -m pip install -r requirements.txt
  )
) else (
  python -c "import streamlit,docx" >nul 2>&1
  if ERRORLEVEL 1 (
    python -m pip install --upgrade pip
    if exist "requirements.txt" (
      python -m pip install -r requirements.txt
    )
  )
)
python -c "import xlrd,win32com.client" >nul 2>&1
if ERRORLEVEL 1 (
  if exist "requirements.txt" (
    python -m pip install -r requirements.txt
  )
)
python -m streamlit run app.py
