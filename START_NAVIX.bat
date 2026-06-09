@echo off
echo Starting NAVIX...

:: Start Qdrant in background
start "Qdrant" /MIN cmd /c "cd /d F:\naveen\qdrant_bin && qdrant.exe --config-path F:\naveen\AGI_Start\config\qdrant_config.yaml"

:: Wait for Qdrant
timeout /t 5 /nobreak > nul

:: Start FastAPI in background
start "FastAPI" /MIN cmd /c "cd /d F:\naveen\AGI_Start && uv run uvicorn app.main:app --host 127.0.0.1 --port 8001"

:: Wait for FastAPI
timeout /t 8 /nobreak > nul

:: Start NAVIX voice
cd /d F:\naveen\AGI_Start
uv run python navix_start.py