from fastapi import APIRouter, BackgroundTasks
from app.services.backup import run_backup
from pathlib import Path
from loguru import logger

router = APIRouter(prefix="/backup", tags=["backup"])

@router.post("/run-now")
async def run_backup_now():
    result = run_backup()
    return result

@router.post("/run")
async def trigger_backup(background_tasks: BackgroundTasks):
    background_tasks.add_task(_do_backup)
    return {"status": "backup started in background"}

@router.get("/list")
async def list_backups():
    backup_dir = Path("F:/naveen/AGI_Start/backups")
    if not backup_dir.exists():
        return {"backups": [], "count": 0}
    zips = sorted(backup_dir.glob("backup_*.zip"),
                 key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "backups": [
            {"name": z.name, "size_kb": round(z.stat().st_size / 1024, 1)}
            for z in zips
        ],
        "count": len(zips)
    }

def _do_backup():
    try:
        result = run_backup()
        logger.info(f"Background backup complete: {result}")
    except Exception as e:
        logger.error(f"Background backup failed: {e}")