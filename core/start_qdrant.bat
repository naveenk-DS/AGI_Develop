@echo off
cd /d F:\naveen\qdrant_bin
start "" /MIN qdrant.exe --config-path F:\naveen\AGI_Start\config\qdrant_config.yaml
echo Qdrant started on port 6333