from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    page_texts: list[str] = []

    for page in reader.pages:
        extracted = page.extract_text() or ""
        cleaned = extracted.strip()

        if cleaned:
            page_texts.append(cleaned)

    return "\n\n".join(page_texts)


def extract_text_from_pdfs(pdf_paths: list[Path]) -> str:
    documents: list[str] = []

    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)

        if text:
            documents.append(text)

    return "\n\n".join(documents)