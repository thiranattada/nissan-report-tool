"""Static (slide_index, shape_index) -> logical table name map for
assets/nissan_template.pptx. Built by opening the REAL client template with
python-pptx and printing every `shape.has_table` shape's index and header
row (see README "Regenerating table_map.py"). This is the single most
fragile artifact in the system (plan Key Risks) — if the client ever
hand-edits the template in PowerPoint and a table shape gets recreated, its
shape index can shift and this map goes stale. `table_writer.validate_template()`
guards against that by failing fast instead of writing to the wrong shape.

Shape names in this deck are Google Slides' auto-generated export names
(e.g. "Google Shape;197;p6") — not human-meaningful, so index-based lookup
is used for now. Recommend renaming shapes in PowerPoint (e.g.
"tbl_incident_summary") next time the template is touched, then switching
this map to name-based lookup, which is far more robust than index-based.

Sections NOT in this map (Executive Summary bullets, title-slide date,
Resource Status / man-hour tables, Privilege User Permission table) are
explicitly out of MVP scope — see plan "Explicitly out of scope for this MVP".
"""

TABLE_MAP = {
    "incident_summary": (5, 2),
    "module_breakdown": (5, 5),
    "trend_inquiry": (6, 2),
    "top5_inquiry_a": (7, 2),
    "top5_inquiry_b": (7, 4),
    "inquiry_detail_carryover_closed": (8, 1),
    "inquiry_detail_carryover_open": (8, 2),
    "trend_service_request": (9, 2),
    "top5_service_request": (10, 2),
    "service_request_detail_carryover_closed": (11, 1),
    "service_request_detail_carryover_open": (11, 2),
    "trend_failure": (12, 3),
    "failure_detail": (13, 2),
    "change_request": (14, 2),
    "problem_management": (15, 2),
    "change_release_management": (16, 2),
}

# Present in the template but intentionally NOT auto-populated this MVP —
# listed here only so validate_template() can still sanity-check they exist,
# without any slide-building code writing to them.
OUT_OF_SCOPE_TABLES = {
    "privilege_user_permission": (17, 5),
    "resource_manhours": (21, 1),
    "resource_working_hours": (22, 0),
    "resource_effort_by_category": (22, 1),
}
