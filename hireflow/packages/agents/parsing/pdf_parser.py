"""PDF → plain text.  Uses pdfplumber for digital PDFs; pytesseract for scanned."""

import io

import pdfplumber


def parse_pdf(data: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    text = "\n".join(text_parts).strip()

    if not text:
        text = _ocr(data)

    return text


def _ocr(data: bytes) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_bytes  # type: ignore[import]
    except ImportError:
        return ""

    images = convert_from_bytes(data, dpi=200)
    pages = [pytesseract.image_to_string(img, lang="eng") for img in images]
    return "\n".join(pages).strip()
