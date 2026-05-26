@echo off
cd /d F:\naveen\AGI_Start\core

if not exist "F:\naveen\AGI_Start\logs" mkdir "F:\naveen\AGI_Start\logs"

echo [%date% %time%] Starting AGI_Start services... >> F:\naveen\AGI_Start\logs\startup.log

:: Start Docker services
docker compose --env-file ..\config\.env up -d >> F:\naveen\AGI_Start\logs\startup.log 2>&1

:: Wait for services to be ready
timeout /t 15 /nobreak > nul

:: Start Python API
cd /d F:\naveen\AGI_Start
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 >> F:\naveen\AGI_Start\logs\startup.log 2>&1