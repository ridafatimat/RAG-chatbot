from typing import Any, Callable, Dict, List, Optional, Tuple


Chunk = Dict[str, Any]
Section = Dict[str, Any]


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).replace("\x00", "").strip()


def _safe_metadata(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _window_end(text: str, start: int, chunk_size: int) -> int:
    """
    Prefer ending at a whitespace boundary without creating tiny chunks.
    """
    hard_end = min(start + chunk_size, len(text))

    if hard_end >= len(text):
        return len(text)

    minimum_end = start + max(int(chunk_size * 0.60), 1)
    boundary = text.rfind(" ", minimum_end, hard_end)

    if boundary <= start:
        boundary = text.rfind("\n", minimum_end, hard_end)

    return boundary if boundary > start else hard_end


def _next_start(text: str, start: int, end: int, overlap: int) -> int:
    if end >= len(text):
        return len(text)

    candidate = max(start + 1, end - overlap)

    # Avoid starting in the middle of a word where practical.
    while candidate < end and candidate < len(text) and not text[candidate].isspace():
        candidate += 1

    while candidate < len(text) and text[candidate].isspace():
        candidate += 1

    return candidate if candidate < end else max(start + 1, end - overlap)


def _chunk_single_text(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int,
    overlap: int,
) -> List[Chunk]:
    text = _clean_text(text)

    if not text:
        return []

    chunks: List[Chunk] = []
    start = 0

    while start < len(text):
        end = _window_end(text, start, chunk_size)
        chunk_text_value = text[start:end].strip()

        if chunk_text_value:
            chunks.append(
                {
                    "text": chunk_text_value,
                    "metadata": dict(metadata),
                }
            )

        if end >= len(text):
            break

        start = _next_start(text, start, end, overlap)

    return chunks


def _build_unit_text_and_spans(
    units: List[Dict[str, Any]],
    number_key: str,
    separator: str,
) -> Tuple[str, List[Tuple[int, int, int]]]:
    parts: List[str] = []
    spans: List[Tuple[int, int, int]] = []
    cursor = 0

    for unit in units:
        unit_text = _clean_text(unit.get("text"))
        unit_number = unit.get(number_key)

        if not unit_text or unit_number is None:
            continue

        if parts:
            parts.append(separator)
            cursor += len(separator)

        start = cursor
        parts.append(unit_text)
        cursor += len(unit_text)
        spans.append((start, cursor, int(unit_number)))

    return "".join(parts), spans


def _chunk_numbered_units(
    units: List[Dict[str, Any]],
    base_metadata: Dict[str, Any],
    number_key: str,
    range_start_key: str,
    range_end_key: str,
    label_builder: Callable[[int, int], str],
    chunk_size: int,
    overlap: int,
    separator: str = "\n",
) -> List[Chunk]:
    combined_text, spans = _build_unit_text_and_spans(
        units=units,
        number_key=number_key,
        separator=separator,
    )

    if not combined_text or not spans:
        return []

    chunks: List[Chunk] = []
    start = 0

    while start < len(combined_text):
        end = _window_end(combined_text, start, chunk_size)
        chunk_value = combined_text[start:end].strip()

        intersecting_numbers = [
            unit_number
            for span_start, span_end, unit_number in spans
            if span_end > start and span_start < end
        ]

        if chunk_value and intersecting_numbers:
            range_start = min(intersecting_numbers)
            range_end = max(intersecting_numbers)
            metadata = dict(base_metadata)
            metadata[range_start_key] = range_start
            metadata[range_end_key] = range_end
            metadata["source_label"] = label_builder(range_start, range_end)

            chunks.append(
                {
                    "text": chunk_value,
                    "metadata": metadata,
                }
            )

        if end >= len(combined_text):
            break

        start = _next_start(combined_text, start, end, overlap)

    return chunks


def _line_label(start: int, end: int) -> str:
    return f"Line {start}" if start == end else f"Lines {start}-{end}"


def _paragraph_label(start: int, end: int) -> str:
    return (
        f"Paragraph {start}"
        if start == end
        else f"Paragraphs {start}-{end}"
    )


def _sheet_row_label(sheet_name: str) -> Callable[[int, int], str]:
    def build(start: int, end: int) -> str:
        prefix = f'Sheet "{sheet_name}"'
        return (
            f"{prefix}, Row {start}"
            if start == end
            else f"{prefix}, Rows {start}-{end}"
        )

    return build


def _table_row_label(table_number: int) -> Callable[[int, int], str]:
    def build(start: int, end: int) -> str:
        return (
            f"Table {table_number}, Row {start}"
            if start == end
            else f"Table {table_number}, Rows {start}-{end}"
        )

    return build


def _normalise_sections(content: Any) -> List[Section]:
    """
    Accept both legacy strings and the structured extraction format.
    """
    if isinstance(content, str):
        text = _clean_text(content)
        return [{"text": text, "metadata": {}}] if text else []

    if isinstance(content, list):
        sections: List[Section] = []

        for item in content:
            sections.extend(_normalise_sections(item))

        return sections

    if not isinstance(content, dict):
        return []

    # Keep spreadsheet sections intact because their row units are required.
    if isinstance(content.get("rows"), list):
        return [content]

    nested = (
        content.get("sections")
        or content.get("pages")
        or content.get("slides")
        or content.get("sheets")
    )

    if isinstance(nested, list):
        return _normalise_sections(nested)

    text = _clean_text(content.get("text") or content.get("content"))

    if not text:
        return []

    return [
        {
            "text": text,
            "metadata": _safe_metadata(content.get("metadata")),
        }
    ]


def chunk_text(
    content: Any,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[Chunk]:
    """
    Split extracted document content into citation-aware chunks.

    Returned shape:
    {
        "text": "...",
        "metadata": {
            "source_type": "pdf",
            "page_number": 2,
            "source_label": "Page 2",
            "chunk_index": 4
        }
    }
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    sections = _normalise_sections(content)
    chunks: List[Chunk] = []
    index = 0

    while index < len(sections):
        section = sections[index]
        metadata = _safe_metadata(section.get("metadata"))

        # CSV/XLSX: chunk rows within the current sheet.
        if isinstance(section.get("rows"), list):
            rows = section.get("rows") or []
            sheet_name = str(metadata.get("sheet_name") or "Data")

            if rows:
                row_chunks = _chunk_numbered_units(
                    units=rows,
                    base_metadata=metadata,
                    number_key="row_number",
                    range_start_key="row_start",
                    range_end_key="row_end",
                    label_builder=_sheet_row_label(sheet_name),
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
                chunks.extend(row_chunks)
            else:
                chunks.extend(
                    _chunk_single_text(
                        text=section.get("text", ""),
                        metadata=metadata,
                        chunk_size=chunk_size,
                        overlap=overlap,
                    )
                )

            index += 1
            continue

        # TXT: combine consecutive line units and preserve line ranges.
        if metadata.get("line_number") is not None:
            units: List[Dict[str, Any]] = []
            base_metadata = {
                key: value
                for key, value in metadata.items()
                if key != "line_number"
            }

            while index < len(sections):
                candidate = sections[index]
                candidate_metadata = _safe_metadata(candidate.get("metadata"))

                if candidate_metadata.get("line_number") is None:
                    break

                units.append(
                    {
                        "text": candidate.get("text", ""),
                        "line_number": candidate_metadata.get("line_number"),
                    }
                )
                index += 1

            chunks.extend(
                _chunk_numbered_units(
                    units=units,
                    base_metadata=base_metadata,
                    number_key="line_number",
                    range_start_key="line_start",
                    range_end_key="line_end",
                    label_builder=_line_label,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
            )
            continue

        # DOCX paragraphs: combine consecutive paragraphs and preserve range.
        if metadata.get("paragraph_number") is not None:
            units = []
            base_metadata = {
                key: value
                for key, value in metadata.items()
                if key != "paragraph_number"
            }

            while index < len(sections):
                candidate = sections[index]
                candidate_metadata = _safe_metadata(candidate.get("metadata"))

                if candidate_metadata.get("paragraph_number") is None:
                    break

                units.append(
                    {
                        "text": candidate.get("text", ""),
                        "paragraph_number": candidate_metadata.get("paragraph_number"),
                    }
                )
                index += 1

            chunks.extend(
                _chunk_numbered_units(
                    units=units,
                    base_metadata=base_metadata,
                    number_key="paragraph_number",
                    range_start_key="paragraph_start",
                    range_end_key="paragraph_end",
                    label_builder=_paragraph_label,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    separator="\n\n",
                )
            )
            continue

        # DOCX tables: combine consecutive rows from the same table.
        if (
            metadata.get("table_number") is not None
            and metadata.get("table_row_number") is not None
        ):
            table_number = int(metadata["table_number"])
            units = []
            base_metadata = {
                key: value
                for key, value in metadata.items()
                if key not in {"table_row_number", "source_label"}
            }

            while index < len(sections):
                candidate = sections[index]
                candidate_metadata = _safe_metadata(candidate.get("metadata"))

                if (
                    candidate_metadata.get("table_number") != table_number
                    or candidate_metadata.get("table_row_number") is None
                ):
                    break

                units.append(
                    {
                        "text": candidate.get("text", ""),
                        "table_row_number": candidate_metadata.get("table_row_number"),
                    }
                )
                index += 1

            chunks.extend(
                _chunk_numbered_units(
                    units=units,
                    base_metadata=base_metadata,
                    number_key="table_row_number",
                    range_start_key="table_row_start",
                    range_end_key="table_row_end",
                    label_builder=_table_row_label(table_number),
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
            )
            continue

        # PDF pages, PPTX slides, and generic legacy sections remain separate
        # so chunks never lose their exact page/slide source.
        chunks.extend(
            _chunk_single_text(
                text=section.get("text", ""),
                metadata=metadata,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )
        index += 1

    final_chunks: List[Chunk] = []

    for chunk in chunks:
        text = _clean_text(chunk.get("text"))

        if not text:
            continue

        metadata = _safe_metadata(chunk.get("metadata"))
        metadata["chunk_index"] = len(final_chunks)

        if not metadata.get("source_label"):
            metadata["source_label"] = f"Chunk {len(final_chunks) + 1}"

        final_chunks.append(
            {
                "text": text,
                "metadata": metadata,
            }
        )

    return final_chunks