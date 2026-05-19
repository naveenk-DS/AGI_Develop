@echo off
cd /d F:\naveen\AGI_Start\core

:: Start Docker services
docker compose --env-file ..\config\.env up -d

:: Wait for Postgres to be ready
timeout /t 20 /nobreak > nul

:: Start Python API
cd /d F:\naveen\AGI_Start
uv run uvicorn app.main:app --host [IP_ADDRESS] --port 8000