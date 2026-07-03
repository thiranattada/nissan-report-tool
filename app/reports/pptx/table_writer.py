from pptx.presentation import Presentation as PresentationType
from pptx.table import Table, _Cell


class TemplateShapeError(RuntimeError):
    """Raised when a mapped (slide_idx, shape_idx) no longer points at a
    table in the template — fail fast instead of silently writing garbage
    or crashing deep inside python-pptx (plan Key Risks: template fragility)."""


def get_table(prs: PresentationType, slide_idx: int, shape_idx: int) -> Table:
    try:
        slide = prs.slides[slide_idx]
        shape = slide.shapes[shape_idx]
    except IndexError as exc:
        raise TemplateShapeError(f"slide={slide_idx} shape={shape_idx} does not exist in template") from exc
    if not shape.has_table:
        raise TemplateShapeError(f"slide={slide_idx} shape={shape_idx} is not a table (template may have changed)")
    return shape.table


def validate_template(prs: PresentationType, table_map: dict[str, tuple[int, int]]) -> None:
    """Call once before writing anything — surfaces a clear error immediately
    if the template has drifted, rather than failing mysteriously mid-build."""
    errors = []
    for name, (slide_idx, shape_idx) in table_map.items():
        try:
            get_table(prs, slide_idx, shape_idx)
        except TemplateShapeError as exc:
            errors.append(f"{name}: {exc}")
    if errors:
        raise TemplateShapeError("Template validation failed:\n" + "\n".join(errors))


def set_run_text(cell: _Cell, text: str) -> None:
    """Sets cell text while preserving existing run-level formatting
    (font/size/color) — replacing the whole text_frame.text resets formatting
    to a default run, which visibly breaks the template's styling."""
    tf = cell.text_frame
    if not tf.paragraphs:
        tf.text = text
        return
    para = tf.paragraphs[0]
    if not para.runs:
        para.text = text
        return
    para.runs[0].text = text
    for extra_run in para.runs[1:]:
        extra_run.text = ""
    # Clear any additional paragraphs beyond the first so stale values from
    # a previous month's row don't linger below the new text.
    for extra_para in tf.paragraphs[1:]:
        for run in extra_para.runs:
            run.text = ""


def write_rows(
    table: Table,
    rows: list[list[str]],
    start_row: int = 1,
    empty_message: str | None = None,
) -> None:
    """Writes `rows` starting at `start_row`, clearing (not deleting) any
    template rows beyond what's written. If `rows` is empty and
    `empty_message` is given, writes it into the first data row's first cell
    instead of leaving a headerless-looking blank table."""
    available_rows = len(table.rows) - start_row
    n_cols = len(table.columns)

    if not rows and empty_message is not None:
        set_run_text(table.cell(start_row, 0), empty_message)
        for col in range(1, n_cols):
            set_run_text(table.cell(start_row, col), "")
        rows_to_clear = range(start_row + 1, len(table.rows))
    else:
        for offset, row_values in enumerate(rows[:available_rows]):
            row_idx = start_row + offset
            for col in range(n_cols):
                value = row_values[col] if col < len(row_values) else ""
                set_run_text(table.cell(row_idx, col), "" if value is None else str(value))
        rows_to_clear = range(start_row + len(rows), len(table.rows))

    for row_idx in rows_to_clear:
        for col in range(n_cols):
            set_run_text(table.cell(row_idx, col), "")
