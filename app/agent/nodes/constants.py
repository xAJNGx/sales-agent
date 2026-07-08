import re

REQUIRED_LEAD_FIELDS = [
    "products",
    "reason",
    "budget",
    "name",
    "email",
    "phone",
]

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TIME_RE = re.compile(r"\d{2}:\d{2}")