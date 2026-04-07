import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file.
    Returns the combined text of all pages.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[PDF Parser] Error reading {pdf_path}: {e}")
        return ""

    return text.strip()
