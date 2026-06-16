import os
import pandas as pd
from pypdf import PdfReader
from docx import Document
from pptx import Presentation


SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".pptx", ".csv", ".xlsx"]


def get_file_extension(file_name: str) -> str:
    """
    Return the file extension in lowercase.
    Example: notes.PDF -> .pdf
    """
    return os.path.splitext(file_name)[1].lower()


def is_supported_file(file_name: str) -> bool:
    """
    Check whether uploaded file type is supported.
    """
    file_extension = get_file_extension(file_name)
    return file_extension in SUPPORTED_EXTENSIONS


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    """
    text = ""

    reader = PdfReader(file_path)

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a .txt file.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        return file.read().strip()


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a Microsoft Word .docx file.
    """
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())

    return "\n".join(paragraphs).strip()


def extract_text_from_pptx(file_path: str) -> str:
    """
    Extract text from a PowerPoint .pptx file.
    """
    presentation = Presentation(file_path)

    slide_texts = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_text = [f"Slide {slide_number}:"]

        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text.append(shape.text.strip())

        slide_texts.append("\n".join(slide_text))

    return "\n\n".join(slide_texts).strip()


def extract_text_from_csv(file_path: str) -> str:
    """
    Extract readable text from a CSV file.
    """
    dataframe = pd.read_csv(file_path)

    if dataframe.empty:
        return ""

    return dataframe.to_string(index=False)


def extract_text_from_excel(file_path: str) -> str:
    """
    Extract readable text from all sheets of an Excel .xlsx file.
    """
    excel_file = pd.ExcelFile(file_path)

    all_sheets_text = []

    for sheet_name in excel_file.sheet_names:
        dataframe = pd.read_excel(file_path, sheet_name=sheet_name)

        sheet_text = f"Sheet: {sheet_name}\n"

        if dataframe.empty:
            sheet_text += "No data found in this sheet."
        else:
            sheet_text += dataframe.to_string(index=False)

        all_sheets_text.append(sheet_text)

    return "\n\n".join(all_sheets_text).strip()


def extract_text_from_document(file_path: str, file_name: str) -> str:
    """
    Main function used by upload route.
    It checks file extension and calls the correct extraction function.
    """
    file_extension = get_file_extension(file_name)

    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if file_extension == ".txt":
        return extract_text_from_txt(file_path)

    if file_extension == ".docx":
        return extract_text_from_docx(file_path)

    if file_extension == ".pptx":
        return extract_text_from_pptx(file_path)

    if file_extension == ".csv":
        return extract_text_from_csv(file_path)

    if file_extension == ".xlsx":
        return extract_text_from_excel(file_path)

    raise ValueError(f"Unsupported file type: {file_extension}")