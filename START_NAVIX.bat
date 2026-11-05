@echo off
echo Starting NAVIX...

:: 1. Start Qdrant vector database in background
start "Qdrant" /MIN cmd /c "cd /d C:\Users\Naveen\AGI_Develop\bin\qdrant && qdrant.exe --config-path C:\Users\Naveen\AGI_Develop\config\qdrant_config.yaml"

:: 2. Wait for Qdrant to be ready
ping 127.0.0.1 -n 4 > nul

:: 3. Start NAVIX system
cd /d C:\Users\Naveen\AGI_Develop
uv run python navix_start.py
