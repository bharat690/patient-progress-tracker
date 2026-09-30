from datetime import date, datetime


DATE_FORMATS = (
    "%m/%d/%Y",
    "%m/%d/%y",
    "%B %d, %Y",
    "%b %d, %Y",
)


def normalize_date(value: str | date | None) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    normalized = value.strip().rstrip(".,")
    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized).isoformat()
    except ValueError:
        pass

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(normalized, date_format).date().isoformat()
        except ValueError:
            continue

    return None
