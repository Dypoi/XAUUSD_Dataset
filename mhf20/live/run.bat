@echo off
REM ==========================================================
REM  MHF-20 Journal - jalankan di laptop Windows (MT5 terbuka)
REM  Aman ditutup kapan saja: state tersimpan otomatis.
REM  Auto-restart bila program berhenti tak terduga.
REM ==========================================================
cd /d "%~dp0"

if not exist ".venv\" (
  echo [setup] Membuat virtual environment...
  python -m venv .venv
  .venv\Scripts\python -m pip install --quiet --upgrade pip
  echo [setup] Memasang dependensi...
  .venv\Scripts\pip install --quiet -r requirements.txt
)

echo.
echo   MHF-20 Journal  --^>  http://127.0.0.1:8765
echo   Ctrl+C untuk berhenti. Data TIDAK hilang.
echo.

:loop
.venv\Scripts\python app.py
echo.
echo [!] Program berhenti. Restart otomatis 5 detik lagi...
echo     (tekan Ctrl+C sekarang untuk keluar total)
timeout /t 5 >nul
goto loop
