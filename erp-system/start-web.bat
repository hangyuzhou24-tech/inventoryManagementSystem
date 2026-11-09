@echo off
chcp 65001 >nul
cd /d "%~dp0web"
echo [启动前端] http://localhost:3000
npm run dev
pause
