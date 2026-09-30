@echo off
chcp 65001 >nul
title LocalLLM - Yerel RAG Asistani
cd /d "%~dp0"

set "PY=python"

where python >nul 2>&1
if errorlevel 1 (
  echo [HATA] Python bulunamadi. https://www.python.org/downloads/ adresinden kurun.
  pause
  exit /b 1
)

rem Sistemdeki Python gerekli paketlere sahipse sanal ortam kurmadan calistir.
python -c "import fastapi, uvicorn, numpy, requests" >nul 2>&1
if errorlevel 1 (
  if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam olusturuluyor...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    echo Bagimliliklar kuruluyor, bu birkac dakika surebilir...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
  )
  set "PY=.venv\Scripts\python.exe"
)

%PY% main.py %*
pause
