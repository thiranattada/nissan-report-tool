import io

from pptx import Presentation

from app.jira.models import ScopeDataBundle
from app.reports.pptx.slides import build_all_sections
from app.reports.pptx.table_map import TABLE_MAP
from app.reports.pptx.table_writer import validate_template


class PptxReportBuilder:
    """Opens a fresh copy of the client's real template (never mutates
    `assets/nissan_template.pptx` itself) and edits table cell contents in
    place, preserving Nissan's exact branding/layout."""

    def __init__(self, template_path: str):
        self.template_path = template_path

    def build(self, bundle: ScopeDataBundle) -> io.BytesIO:
        prs = Presentation(self.template_path)
        validate_template(prs, TABLE_MAP)
        build_all_sections(prs, bundle)

        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        return buf
