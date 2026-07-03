# Nissan Report Tool

Generates the monthly "Service Management Monthly Report" PowerPoint and the
Jira Export Excel workbook from live Jira Cloud data, replacing the manual
process the Technical Operation Support team does today.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in real values, see "Before this is usable" below
uvicorn app.main:app --reload
```

Open http://localhost:8000, log in with `APP_BASIC_AUTH_USER` /
`APP_BASIC_AUTH_PASSWORD` from your `.env`, pick a date range, and export.

## Testing

```bash
pytest tests/ -v
```

All current tests are pure-logic (JQL string construction, fiscal-year math,
SLA calculators, auth gate) and run without a live Jira connection.

## Before this is usable against real Nissan data

These are placeholders in the code right now and MUST be confirmed/replaced
before trusting the output for an actual client report:

1. **Jira credentials** (`.env`): `JIRA_BASE_URL`, `JIRA_EMAIL`,
   `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`.
2. **Custom field IDs** in `app/jira/fields.py` (Route Cause, Countermeasure,
   Impact Level, Category) — currently placeholder `customfield_101xx` IDs.
   Get the real ones from `GET /rest/api/3/field` on your Jira instance.
3. **Category field values** in `app/reports/common/aggregations.py`
   (`INCIDENT_SUB_CATEGORIES`, `OTHER_CATEGORIES`) — confirm these match the
   actual dropdown options configured on the Category custom field.
4. **Priority → SLA level mapping** in `app/reports/common/sla.py`
   (`PRIORITY_TO_LEVEL`) — currently Jira's default priority names
   (Highest/High/Medium); the real Nissan project may use custom names.
5. **Business hours** in `app/clients/nissan.py` — currently defaults to
   09:00–17:00 Mon–Fri; confirm Nissan's actual 8x5 support window clock
   hours.
6. **Working-day SLA boundary** in `app/reports/common/sla.py` — currently
   assumes the creation day itself doesn't count toward the 2/3-day Inquiry
   / Service Request targets. Confirm against a real historical example.

## Known limitations (by design, for this MVP)

- **Man-hour/Resource Status Report and Privilege User Permission** sections
  of the PPT are intentionally NOT auto-populated — they don't come from
  Jira. Edit those slides by hand after export, same as today.
- **Top 5 tables**: the real template groups Inquiry issues by two different
  dimensions we haven't identified a matching Jira field for yet; both
  currently group by `route_cause` as a stand-in (see
  `app/reports/pptx/slides.py` module docstring).
- **Multi-line cells** (e.g. the Incident Summary category breakdown) can
  carry over a few trailing blank lines from the original template's cell
  structure — cosmetic only, doesn't affect the numbers. Worth tightening
  once someone reviews a real generated deck.
- Single shared login for the whole team (`APP_BASIC_AUTH_USER/PASSWORD`),
  no per-user accounts — fine for an internal single-team MVP.

## Regenerating `app/reports/pptx/table_map.py`

If the Nissan `.pptx` template is ever edited by hand in PowerPoint, table
shape indices can shift. Regenerate the map by running:

```bash
python3 -c "
from pptx import Presentation
prs = Presentation('assets/nissan_template.pptx')
for i, slide in enumerate(prs.slides):
    for j, shape in enumerate(slide.shapes):
        if shape.has_table:
            print(i, j, [c.text for c in shape.table.rows[0].cells])
"
```

and update `TABLE_MAP` to match. `PptxReportBuilder` calls
`validate_template()` on every build, so a stale map fails fast with a clear
error instead of silently writing to the wrong table.

## Adding another client (KTC, MEA, MTS)

Add a sibling to `app/clients/nissan.py` with that client's
`BusinessHoursConfig` and template path, then parameterize `app/main.py`'s
endpoints by a `client` field instead of hardcoding Nissan. Not needed for
this MVP — Nissan only.
