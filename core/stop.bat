@echo off
echo Stopping AGI_Start...

cd /d F:\naveen\AGI_Start\core
docker compose --env-file ..\config\.env down

echo Stopped.
pause
