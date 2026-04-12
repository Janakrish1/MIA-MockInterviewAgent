"""Resume upload: store PDF in documents/resumes and extract text with PyPDF."""
import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services import resume_upload

router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str | None = Form(None),  # optional; if set, store under documents/resumes/{user_id}/
):
    """
    Upload a resume PDF. It is saved under backend/documents/resumes/ (or resumes/{user_id}/).
    Returns extracted text for use as resume_summary in the interview pipeline.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    try:
        resume_id, resume_text = await asyncio.to_thread(
            resume_upload.save_and_extract_resume,
            content,
            user_id=user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "resume_id": resume_id,
        "resume_text": resume_text,
    }
