"""Nissan-specific configuration. Adding another client (KTC, MEA, MTS)
later means adding a sibling module here + registering it in config.py's
CLIENT_REGISTRY — no changes to the report-generation code itself."""

from app.reports.common.sla import BusinessHoursConfig

NISSAN_BUSINESS_HOURS = BusinessHoursConfig(is_24x7=False)  # 8x5 Mon-Fri, placeholder clock hours

NISSAN_TEMPLATE_PATH = "assets/nissan_template.pptx"
