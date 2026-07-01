import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger

BASE = Path("F:/naveen/AGI_Start")
BACKUP_DIR = BASE / "backups"
DATA_DIR = BASE / "data"

def run_backup() -> dict:
    BACKUP_DIR.mkdir(exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"backup_{date_str}"
    results = {}

    try:
        pg_dump_file = BACKUP_DIR / f"postgres_{date_str}.sql"
        result = subprocess.run([
            "docker", "exec", "core-postgres-1",
            "pg_dump", "-U", "appuser", "myaiproduct"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            pg_dump_file.write_text(result.stdout, encoding="utf-8")
            results["postgres"] = f"OK — {len(result.stdout)} chars"
            logger.info(f"Postgres dump OK")
        else:
            results["postgres"] = f"FAILED: {result.stderr[:100]}"
    except Exception as e:
        results["postgres"] = f"ERROR: {str(e)}"

    try:
        qdrant_src = DATA_DIR / "qdrant"
        qdrant_backup = BACKUP_DIR / f"qdrant_{date_str}"
        if qdrant_src.exists():
            shutil.copytree(str(qdrant_src), str(qdrant_backup))
            results["qdrant"] = "OK"
        else:
            results["qdrant"] = "skipped"
    except Exception as e:
        results["qdrant"] = f"ERROR: {str(e)}"

    try:
        zip_path = BACKUP_DIR / backup_name
        shutil.make_archive(str(zip_path), "zip", str(BACKUP_DIR))
        results["zip"] = f"{backup_name}.zip"
    except Exception as e:
        results["zip"] = f"ERROR: {str(e)}"

    try:
        zips = sorted(BACKUP_DIR.glob("backup_*.zip"),
                     key=lambda f: f.stat().st_mtime)
        for old in zips[:-7]:
            old.unlink()
        results["cleanup"] = f"kept last {min(len(zips), 7)} backups"
    except Exception as e:
        results["cleanup"] = f"ERROR: {str(e)}"

    results["timestamp"] = date_str
    results["status"] = "completed"
    return results