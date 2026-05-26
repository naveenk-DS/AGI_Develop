import time
import httpx
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

WATCH_FOLDER = Path("F:/naveen/AGI_Start/watch")
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

import threading

stop_event = threading.Event()

def start_watcher():
    WATCH_FOLDER.mkdir(exist_ok=True)
    (WATCH_FOLDER / "processed").mkdir(exist_ok=True)

    handler = NewFileHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_FOLDER), recursive=False)
    observer.start()
    logger.info(f"Watching folder: {WATCH_FOLDER}")

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    observer.stop()
    observer.join()

if __name__ == "__main__":
    try:
        start_watcher()
    except KeyboardInterrupt:
        stop_event.set()