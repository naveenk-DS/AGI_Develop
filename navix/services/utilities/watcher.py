import time
import httpx
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

WATCH_FOLDER = Path("C:/Users/Naveen/AGI_Develop/watch")
API_URL = "http://127.0.0.1:8001/rag/ingest-path"

SUPPORTED = {".txt", ".md", ".csv", ".pdf", ".docx"}

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.suffix.lower() not in SUPPORTED:
            logger.warning(f"Skipped unsupported file: {path.name}")
            return

        logger.info(f"New file detected: {path.name}")
        time.sleep(1)  # wait for file to finish writing

        try:
            r = httpx.post(API_URL, json={
                "file_path": str(path).replace("\\", "/"),
                "doc_name": path.name
            }, timeout=120)

            if r.status_code == 200:
                data = r.json()
                logger.info(f"Ingested: {path.name} — {data['chunks_stored']} chunks stored")
                # move to processed folder
                processed = WATCH_FOLDER / "processed"
                processed.mkdir(exist_ok=True)
                path.rename(processed / path.name)
            else:
                logger.error(f"Ingest failed: {r.text}")

        except Exception as e:
            logger.error(f"Watcher error: {e}")

_observer = None

def start_watcher():
    global _observer
    try:
        WATCH_FOLDER.mkdir(exist_ok=True)
        (WATCH_FOLDER / "processed").mkdir(exist_ok=True)

        handler = NewFileHandler()
        _observer = Observer()
        _observer.schedule(handler, str(WATCH_FOLDER), recursive=False)
        _observer.start()
        logger.info(f"Watching folder: {WATCH_FOLDER}")
    except Exception as e:
        logger.warning(f"Watcher start error: {e}")

def stop_watcher():
    global _observer
    if _observer:
        try:
            _observer.stop()
            _observer.join(timeout=2)
        except Exception:
            pass

if __name__ == "__main__":
    start_watcher()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watcher()
