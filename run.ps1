Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting HeadlineDiff Services..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Launch FastAPI Backend
Write-Host "Launching Backend server (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -Title "HeadlineDiff Backend"

# Launch Vite Frontend
Write-Host "Launching Frontend server (Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -Title "HeadlineDiff Frontend"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "HeadlineDiff is launching!" -ForegroundColor Green
Write-Host "Backend API: http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
