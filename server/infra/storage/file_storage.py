import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from config.logging import get_logger

class FileStorage:
    """Helper for file storage operations"""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("storage.file")

    async def save_pdf_file(self, file: UploadFile) -> str:
        """Save uploaded PDF file and return the file path"""
        # Validate file type
        if not file.content_type or not file.content_type.startswith('application/pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Generate unique filename
        file_extension = ".pdf"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename

        try:
            # Read and save file content
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)

            return str(file_path)
        except Exception as exc:
            self.logger.exception("Failed to save uploaded PDF file to %s", file_path)
            raise HTTPException(
                status_code=500,
                detail="Failed to save file"
            ) from exc

    def delete_file(self, file_path: str) -> None:
        """Delete a file from storage"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            self.logger.warning("Failed to delete file: %s", file_path, exc_info=True)

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        return os.path.exists(file_path)
