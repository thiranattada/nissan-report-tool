"""Shared counting/grouping helpers used by both the Excel and PPT builders,
so aggregation logic isn't re-derived per output format."""

from collections import Counter
from dataclasses import dataclass

from app.jira.models import Issue, ScopeDataBundle
from app.reports.common.scope import fiscal_month_index

# Values of the "Category" custom field this report expects. Confirm these
# match the real values configured on the Nissan project (plan Open Item #2)
# before relying on this for a real report — a mismatch here silently drops
# issues into no category rather than erroring.
INCIDENT_SUB_CATEGORIES = ["Failure", "Inquiry", "Service Request"]
OTHER_CATEGORIES = ["Problem Management", "Enhancement", "Change/Release Management"]

FISCAL_MONTH_LABELS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]


def count_by_category(issues: list[Issue]) -> Counter:
    return Counter(issue.category for issue in issues if issue.category)


@dataclass
class CategoryCounts:
    carry_over: int
    started: int
    closed: int

    @property
    def on_process(self) -> int:
        return self.carry_over + self.started - self.closed


def incident_summary_counts(bundle: ScopeDataBundle) -> dict[str, CategoryCounts]:
    """One CategoryCounts per category value seen across the four Jira-query
    buckets (Carry over / Started / Closed), keyed by the Category field."""
    carry_over = count_by_category(bundle.open_at_period_start)
    started = count_by_category(bundle.current_period)
    closed = count_by_category(bundle.closed_during_period)

    all_categories = INCIDENT_SUB_CATEGORIES + OTHER_CATEGORIES
    return {
        category: CategoryCounts(
            carry_over=carry_over.get(category, 0),
            started=started.get(category, 0),
            closed=closed.get(category, 0),
        )
        for category in all_categories
    }


def module_breakdown(issues: list[Issue]) -> list[tuple[str, int]]:
    """Counts issues by component ("Module" in the report); an issue with
    multiple components is counted once per component, matching how the
    sample report's single "All Module" row behaves for an all-one-module
    project."""
    counter: Counter = Counter()
    for issue in issues:
        if issue.components:
            counter.update(issue.components)
        else:
            counter["All Module"] += 1
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def fiscal_month_trend(issues: list[Issue], category: str) -> list[int]:
    """12 counts, April-first, of issues in `category` created in each
    fiscal month — feeds the "FY.. Apr May Jun ..." trend tables."""
    counts = [0] * 12
    for issue in issues:
        if issue.category != category or issue.created is None:
            continue
        counts[fiscal_month_index(issue.created.date())] += 1
    return counts


def top_n_by(issues: list[Issue], key_fn, n: int = 5) -> list[tuple[str, int]]:
    counter: Counter = Counter(key_fn(i) for i in issues if key_fn(i))
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
