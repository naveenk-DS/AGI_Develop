@echo off
echo Starting NAVIX services...

echo Starting Qdrant...
cd /d F:\naveen\qdrant_bin
start "" /MIN qdrant.exe --config-path F:\naveen\AGI_Start\config\qdrant_config.yaml

echo Waiting for Qdrant...
timeout /t 5 /nobreak > nul

echo Starting FastAPI...
cd /d F:\naveen\AGI_Start
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001

pause