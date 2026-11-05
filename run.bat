@echo off
title ProctorAI - Smart Exam Proctoring System
cd /d "%~dp0"

echo ============================================================
echo   PROCTORAI - HE THONG GIAM SAT PHONG THI THONG MINH
echo   Samsung Innovation Campus - Capstone Project
echo ============================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Khong tim thay moi truong ao .venv!
    echo Vui long kiem tra lai thu muc cai dat.
    pause
    exit /b 1
)

echo [*] Dang kich hoat moi truong ao Python...
call .venv\Scripts\activate.bat

echo [*] Dang khoi dong trinh duyet...
start "" http://127.0.0.1:8000

echo [*] Dang khoi chay may chu ProctorAI...
python main.py

pause
