import os
from typing import Any, Dict, List

import pandas as pd
from docx import Document
from pptx import Presentation
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".pptx", ".csv", ".xlsx"]


SourceSection = Dict[str, Any]


def get_file_extension(file_name: str) -> str:
    """
    Return the file extension in lowercase.
    Example: notes.PDF -> .pdf
    """
    return os.path.splitext(file_name)[1].lower()


def is_supported_file(file_name: str) -> bool:
    """
    Check whether the uploaded file type is supported.
    """
    return get_file_extension(file_name) in SUPPORTED_EXTENSIONS


def _clean_text(value: Any) -> str:
    """
    Convert an extracted value into clean text without destroying
    intentional internal line breaks.
    """
    if value is None:
        return ""

    text = str(value).replace("\x00", "")
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _cell_to_text(value: Any) -> str:
    """
    Convert a spreadsheet cell into stable readable text.
    """
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def _dataframe_rows(dataframe: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert dataframe records into readable row units.

    row_number uses the original spreadsheet-style numbering:
    row 1 is the header, so the first data record is row 2.
    """
    rows: List[Dict[str, Any]] = []
    columns = [str(column).strip() for column in dataframe.columns]

    for dataframe_index, (_, record) in enumerate(dataframe.iterrows(), start=2):
        values = []

        for column in columns:
            value = _cell_to_text(record.get(column, ""))
            if value:
                values.append(f"{column}: {value}")

        if not values:
            continue

        rows.append(
            {
                "text": " | ".join(values),
                "row_number": dataframe_index,
            }
        )

    return rows


def extract_text_from_pdf(file_path: str) -> List[SourceSection]:
    """
    Extract a PDF page by page so every chunk can retain its page number.
    """
    reader = PdfReader(file_path)
    pages: List[SourceSection] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = _clean_text(page.extract_text() or "")

        if not page_text:
            continue

        pages.append(
            {
                "text": page_text,
                "metadata": {
                    "source_type": "pdf",
                    "page_number": page_number,
                    "source_label": f"Page {page_number}",
                },
            }
        )

    return pages


def extract_text_from_txt(file_path: str) -> List[SourceSection]:
    """
    Extract a text file line by line. The chunking service later combines
    adjacent lines while preserving the resulting line range.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        raw_text = file.read()

    lines: List[SourceSection] = []

    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line_text = _clean_text(line)

        if not line_text:
            continue

        lines.append(
            {
                "text": line_text,
                "metadata": {
                    "source_type": "txt",
                    "line_number": line_number,
                },
            }
        )

    # A single-line file may not contain a line break, but splitlines still
    # returns the content. This fallback mainly protects unusual empty inputs.
    if not lines:
        text = _clean_text(raw_text)
        if text:
            lines.append(
                {
                    "text": text,
                    "metadata": {
                        "source_type": "txt",
                        "line_number": 1,
                    },
                }
            )

    return lines


def extract_text_from_docx(file_path: str) -> List[SourceSection]:
    """
    Extract Word paragraphs and table rows with citation metadata.

    Paragraphs are numbered according to non-empty paragraphs. Table rows are
    appended after paragraph content and retain table/row labels.
    """
    document = Document(file_path)
    sections: List[SourceSection] = []

    paragraph_number = 0

    for paragraph in document.paragraphs:
        paragraph_text = _clean_text(paragraph.text)

        if not paragraph_text:
            continue

        paragraph_number += 1
        sections.append(
            {
                "text": paragraph_text,
                "metadata": {
                    "source_type": "docx",
                    "paragraph_number": paragraph_number,
                },
            }
        )

    for table_number, table in enumerate(document.tables, start=1):
        for row_number, row in enumerate(table.rows, start=1):
            cells = []

            for cell in row.cells:
                cell_text = _clean_text(cell.text)
                if cell_text:
                    cells.append(cell_text)

            if not cells:
                continue

            sections.append(
                {
                    "text": " | ".join(cells),
                    "metadata": {
                        "source_type": "docx",
                        "table_number": table_number,
                        "table_row_number": row_number,
                    },
                }
            )

    return sections


def extract_text_from_pptx(file_path: str) -> List[SourceSection]:
    """
    Extract PowerPoint text slide by slide.
    """
    presentation = Presentation(file_path)
    slides: List[SourceSection] = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_parts: List[str] = []

        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                shape_text = _clean_text(shape.text)
                if shape_text:
                    slide_parts.append(shape_text)

            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    row_cells = []

                    for cell in row.cells:
                        cell_text = _clean_text(cell.text)
                        if cell_text:
                            row_cells.append(cell_text)

                    if row_cells:
                        slide_parts.append(" | ".join(row_cells))

        slide_text = "\n".join(slide_parts).strip()

        if not slide_text:
            continue

        slides.append(
            {
                "text": slide_text,
                "metadata": {
                    "source_type": "pptx",
                    "slide_number": slide_number,
                    "source_label": f"Slide {slide_number}",
                },
            }
        )

    return slides


def extract_text_from_csv(file_path: str) -> List[SourceSection]:
    """
    Extract CSV data as row units so citations can show row ranges.
    """
    dataframe = pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False,
    )

    if dataframe.empty and len(dataframe.columns) == 0:
        return []

    rows = _dataframe_rows(dataframe)
    header_text = "Columns: " + " | ".join(str(column) for column in dataframe.columns)
    full_text_parts = [header_text]
    full_text_parts.extend(row["text"] for row in rows)

    return [
        {
            "text": "\n".join(full_text_parts).strip(),
            "rows": rows,
            "metadata": {
                "source_type": "csv",
                "sheet_name": "CSV",
                "source_label": "CSV data",
            },
        }
    ]


def extract_text_from_excel(file_path: str) -> List[SourceSection]:
    """
    Extract every Excel sheet while preserving sheet names and row numbers.
    """
    excel_file = pd.ExcelFile(file_path)
    sheets: List[SourceSection] = []

    for sheet_name in excel_file.sheet_names:
        dataframe = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            dtype=str,
            keep_default_na=False,
        )

        if dataframe.empty and len(dataframe.columns) == 0:
            continue

        rows = _dataframe_rows(dataframe)
        header_text = "Columns: " + " | ".join(
            str(column) for column in dataframe.columns
        )
        full_text_parts = [header_text]
        full_text_parts.extend(row["text"] for row in rows)

        sheets.append(
            {
                "text": "\n".join(full_text_parts).strip(),
                "rows": rows,
                "metadata": {
                    "source_type": "xlsx",
                    "sheet_name": str(sheet_name),
                    "source_label": f'Sheet "{sheet_name}"',
                },
            }
        )

    return sheets


def extract_text_from_document(file_path: str, file_name: str) -> List[SourceSection]:
    """
    Main extraction function used by the upload route.

    It returns structured source sections rather than one plain string so
    chunk metadata can retain page, slide, paragraph, sheet, and row details.
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