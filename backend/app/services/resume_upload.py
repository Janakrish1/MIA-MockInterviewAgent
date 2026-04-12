"""Store uploaded resume PDFs and extract text with PyPDF."""
import uuid
from pathlib import Path

from pypdf import PdfReader

# Base directory for uploaded documents (resumes). Created on first use.
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent.parent / "documents"
RESUMES_DIR = DOCUMENTS_DIR / "resumes"

# Max file size 5MB
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024


def _ensure_resumes_dir(user_id: str | None) -> Path:
    """Return directory for resumes; create if needed. Optional user_id for per-user folder."""
    if user_id:
        path = RESUMES_DIR / _safe_user_id(user_id)
    else:
        path = RESUMES_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_user_id(user_id: str) -> str:
    """Keep only safe chars for directory name."""
    return "".join(c for c in user_id if c.isalnum() or c in "-_")[:64] or "default"


def save_and_extract_resume(
    file_content: bytes,
    *,
    user_id: str | None = None,
) -> tuple[str, str]:
    """
    Save PDF to documents/resumes (or documents/resumes/{user_id}) and extract text.
    Returns (resume_id, extracted_text).
    """
    if len(file_content) > MAX_RESUME_SIZE_BYTES:
        raise ValueError(f"Resume must be under {MAX_RESUME_SIZE_BYTES // (1024*1024)}MB")

    root = _ensure_resumes_dir(user_id)
    resume_id = str(uuid.uuid4())
    pdf_path = root / f"{resume_id}.pdf"
    txt_path = root / f"{resume_id}.txt"

    pdf_path.write_bytes(file_content)

    try:
        reader = PdfReader(pdf_path)
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        extracted = "\n".join(parts).strip()
    except Exception as e:
        raise ValueError(f"Could not parse PDF: {e}") from e

    if extracted:
        txt_path.write_text(extracted, encoding="utf-8")

    return resume_id, extracted or "(No text extracted from PDF.)"
