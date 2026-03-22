import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException

class FileStorage:
    """Helper for file storage operations"""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

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
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )

    def delete_file(self, file_path: str) -> None:
        """Delete a file from storage"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            # Silently ignore deletion errors for now
            pass

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        return os.path.exists(file_path)