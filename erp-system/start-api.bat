@echo off
chcp 65001 >nul
cd /d "%~dp0api"
echo [启动后端] http://127.0.0.1:8000/docs
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
pause
