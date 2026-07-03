from collections import Counter

from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from app.jira import fields as F
from app.jira.models import Issue

HEADER_FONT = Font(bold=True)


def _autosize(ws: Worksheet) -> None:
    for column_cells in ws.columns:
        length = max((len(str(cell.value)) for cell in column_cells if cell.value is not None), default=8)
        ws.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 60)


def write_raw_sheet(ws: Worksheet, issues: list[Issue]) -> None:
    """Sheet 1: one row per issue, one column per field we track (matches the
    sample's "Jira Export Excel CSV (all fields)" sheet)."""
    columns = ["key"] + F.ALL_FIELDS
    headers = [F.FIELD_LABELS.get(c, c) for c in columns]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = HEADER_FONT

    for issue in issues:
        row = [
            issue.key,
            issue.summary,
            issue.issue_type,
            issue.status,
            issue.priority,
            issue.created.isoformat() if issue.created else None,
            issue.resolved.isoformat() if issue.resolved else None,
            issue.assignee,
            issue.reporter,
            ", ".join(issue.components),
            ", ".join(issue.labels),
            issue.route_cause,
            issue.countermeasure,
            issue.impact_level,
            issue.category,
        ]
        ws.append(row)

    _autosize(ws)


def _write_pivot(ws: Worksheet, title_left: str, title_right: str, counts: Counter) -> None:
    ws.append([title_left, title_right])
    for cell in ws[1]:
        cell.font = HEADER_FONT
    for label, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0] or "")):
        ws.append([label or "(none)", count])
    _autosize(ws)


def write_pivot_by_issue_type(ws: Worksheet, issues: list[Issue]) -> None:
    counts = Counter(issue.issue_type for issue in issues)
    _write_pivot(ws, "Issue Type", "Count", counts)


def write_pivot_by_priority(ws: Worksheet, issues: list[Issue]) -> None:
    counts = Counter(issue.priority for issue in issues)
    _write_pivot(ws, "Priority", "Count", counts)
