import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ResumeParsingError(Exception):
    """Raised when resume text cannot be extracted."""


def extract_text_from_resume(file_field) -> str:
    if not file_field:
        raise ResumeParsingError("No resume file was provided.")

    suffix = Path(file_field.name).suffix.lower()
    if suffix != '.pdf':
        raise ResumeParsingError("AI resume analysis currently supports PDF files only.")

    try:
        from pypdf import PdfReader

        file_field.open('rb')
        reader = PdfReader(file_field)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ''
            if text.strip():
                pages.append(text.strip())
        text = '\n\n'.join(pages).strip()
    except Exception as exc:
        logger.exception("Failed to extract text from resume %s", file_field.name)
        raise ResumeParsingError("Could not extract text from the uploaded PDF.") from exc
    finally:
        try:
            file_field.close()
        except Exception:
            logger.debug("Resume file close failed after parsing.", exc_info=True)

    if not text:
        raise ResumeParsingError("No readable text was found in the uploaded PDF.")

    return text
