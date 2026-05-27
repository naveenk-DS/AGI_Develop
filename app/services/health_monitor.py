import asyncio
import subprocess
import httpx
from loguru import logger
from datetime import datetime

SERVICES = {
    "ollama":  "http://127.0.0.1:11434/api/tags",
    "qdrant":  "http://127.0.0.1:6333/healthz",
    "n8n":     "http://127.0.0.1:5678/healthz"
}

DOCKER_SERVICES = {
    "qdrant": "core-qdrant-1",
    "n8n":    "core-n8n-1"
}

health_status = {
    "ollama": True,
    "qdrant": True,
    "n8n":    True,
    "last_check": None
}

async def check_service(name: str, url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            return r.status_code == 200
    except:
        return False

async def restart_docker_service(container_name: str):
    try:
        subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True, timeout=30
        )
        logger.info(f"Restarted Docker container: {container_name}")
    except Exception as e:
        logger.error(f"Could not restart {container_name}: {e}")

async def run_health_check():
    global health_status
    health_status["last_check"] = datetime.utcnow().isoformat()

    for name, url in SERVICES.items():
        is_healthy = await check_service(name, url)

        if not is_healthy and health_status.get(name, True):
            logger.warning(f"Service DOWN: {name}")
            if name in DOCKER_SERVICES:
                logger.info(f"Auto-restarting: {name}")
                await restart_docker_service(DOCKER_SERVICES[name])

        elif is_healthy and not health_status.get(name, True):
            logger.info(f"Service RECOVERED: {name}")

        health_status[name] = is_healthy

    all_healthy = all(health_status[s] for s in SERVICES)
    if all_healthy:
        logger.debug("All services healthy")
    else:
        failed = [s for s in SERVICES if not health_status[s]]
        logger.warning(f"Unhealthy services: {failed}")

    return health_status.copy()

async def start_health_monitor(interval: int = 60):
    logger.info(f"Health monitor started — checking every {interval}s")
    while True:
        try:
            await run_health_check()
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
        await asyncio.sleep(interval)