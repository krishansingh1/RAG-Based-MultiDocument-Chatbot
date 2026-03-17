from PyPDF2 import PdfReader


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text


if __name__ == "__main__":
    pdf_path = "Individual_Report_Solution_Internet_and_Cloud_Computing.pdf"
    reader = PdfReader(pdf_path)
    text = get_pdf_text([pdf_path])
    print(f"Extracted {len(text)} characters")
    print(f"Number of pages: {len(reader.pages)}")
    print(f"First page text: {reader.pages[0].extract_text()[:500]}")
    