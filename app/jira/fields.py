"""Central field-ID registry for the Nissan Jira project.

Custom field IDs are instance-specific and must be confirmed against the real
project (GET /rest/api/3/field, or open any issue's "..." > Edit screen and
inspect the field's URL/id). The placeholders below are NOT real IDs — replace
them before running against live Jira. See plan Open Items #2.
"""

FIELD_ROUTE_CAUSE = "customfield_10100"  # TODO: confirm real ID
FIELD_COUNTERMEASURE = "customfield_10101"  # TODO: confirm real ID
FIELD_IMPACT_LEVEL = "customfield_10102"  # TODO: confirm real ID
FIELD_CATEGORY = "customfield_10103"  # TODO: confirm real ID (Failure/Inquiry/Service Request/etc.)

STANDARD_FIELDS = [
    "summary",
    "issuetype",
    "status",
    "priority",
    "created",
    "resolutiondate",
    "assignee",
    "reporter",
    "components",
    "labels",
]

CUSTOM_FIELDS = [
    FIELD_ROUTE_CAUSE,
    FIELD_COUNTERMEASURE,
    FIELD_IMPACT_LEVEL,
    FIELD_CATEGORY,
]

ALL_FIELDS = STANDARD_FIELDS + CUSTOM_FIELDS

# Human-readable column headers for the Excel raw-export sheet, in the same
# order as ALL_FIELDS plus the leading "key" column added by the caller.
FIELD_LABELS = {
    "key": "Issue Key",
    "summary": "Summary",
    "issuetype": "Issue Type",
    "status": "Status",
    "priority": "Priority",
    "created": "Created",
    "resolutiondate": "Resolved",
    "assignee": "Assignee",
    "reporter": "Reporter",
    "components": "Components",
    "labels": "Labels",
    FIELD_ROUTE_CAUSE: "Route Cause",
    FIELD_COUNTERMEASURE: "Countermeasure",
    FIELD_IMPACT_LEVEL: "Impact Level",
    FIELD_CATEGORY: "Category",
}
