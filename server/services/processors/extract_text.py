from typing import Dict, Any, List
import aiofiles
import PyPDF2
import io

from .base import BaseNodeProcessor
from errors import ProcessingError

class ExtractTextProcessor(BaseNodeProcessor):
    """Processor for extracting text from PDF files"""

    async def process(self, input_data: str, config: Dict[str, Any]) -> str:
        """Process text extraction from PDF file path"""
        try:
            # input_data should be the file path to the PDF
            file_path = input_data

            if not file_path:
                raise ProcessingError("Input file is missing")

            # Read PDF file and extract text
            async with aiofiles.open(file_path, 'rb') as file:
                pdf_content = await file.read()
                text = await self._extract_pdf_text(pdf_content, config)
                return text

        except FileNotFoundError as exc:
            raise ProcessingError("Input PDF file could not be found") from exc
        except ProcessingError:
            raise
        except Exception as exc:
            raise ProcessingError("Text extraction failed") from exc

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate node configuration"""
        # No required configuration for text extraction
        pass

    def get_required_config_keys(self) -> List[str]:
        """Return list of required configuration keys"""
        return []

    async def _extract_pdf_text(self, pdf_content: bytes, config: Dict[str, Any]) -> str:
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_parts = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()

                if page_text.strip():
                    text_parts.append(page_text)

            # Join pages with newline for simplicity
            extracted_text = '\n'.join(text_parts)

            # Clean up text if requested
            if config.get("clean_text", True):
                extracted_text = self._clean_extracted_text(extracted_text)

            return extracted_text

        except ProcessingError:
            raise
        except Exception as exc:
            raise ProcessingError("PDF text extraction failed") from exc

    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text"""
        import re

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text
