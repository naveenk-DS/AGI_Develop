@echo off
echo Starting NAVIX...

:: Start Qdrant in background
start "Qdrant" /MIN cmd /c "cd /d F:\naveen\qdrant_bin && qdrant.exe --config-path F:\naveen\AGI_Start\config\qdrant_config.yaml"

:: Wait for Qdrant
ping 127.0.0.1 -n 6 > nul



:: Start NAVIX voice
cd /d F:\naveen\AGI_Start
uv run python navix_start.py