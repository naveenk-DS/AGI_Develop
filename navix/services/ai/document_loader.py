from pathlib import Path
from loguru import logger
import pandas as pd

def load_document(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if suffix == ".txt" or suffix == ".md":
        return path.read_text(encoding="utf-8", errors="ignore")

    elif suffix == ".pdf":
        return _load_pdf(path)

    elif suffix == ".docx":
        return _load_docx(path)

    elif suffix == ".csv":
        return _load_csv(path)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def _load_pdf(path: Path) -> str:
    import fitz  # pymupdf
    doc = fitz.open(str(path))
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    logger.info(f"PDF loaded: {path.name} — {len(text)} chars")
    return text

def _load_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    logger.info(f"DOCX loaded: {path.name} — {len(text)} chars")
    return text

def _load_csv(path: Path) -> str:
    df = pd.read_csv(str(path))
    # convert each row to readable text
    rows = []
    for _, row in df.iterrows():
        row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
        rows.append(row_text)
    text = "\n".join(rows)
    logger.info(f"CSV loaded: {path.name} — {len(df)} rows")
    return text

def get_supported_extensions() -> list:
    return [".txt", ".md", ".pdf", ".docx", ".csv"]