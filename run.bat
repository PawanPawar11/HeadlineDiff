@echo off
echo ==========================================
echo Starting HeadlineDiff Services...
echo ==========================================

REM Start FastAPI Backend
echo Launching Backend server (FastAPI)...
start "HeadlineDiff Backend" cmd /c "cd backend && venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

REM Start Vite Frontend
echo Launching Frontend server (Vite)...
start "HeadlineDiff Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo ==========================================
echo HeadlineDiff is now launching!
echo Backend API: http://127.0.0.1:8000/api/health
echo Frontend: http://localhost:5173
echo ==========================================
echo.
pause
