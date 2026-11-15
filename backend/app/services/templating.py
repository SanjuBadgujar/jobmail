import re

from email_validator import EmailNotValidError, validate_email

_VAR = re.compile(r"\{\{\s*(name|company|position)\s*\}\}")


def render(template: str, rec) -> str:
    vals = {"name": rec.name or "Hiring Team", "company": rec.company or "your company", "position": rec.position or "open"}
    return _VAR.sub(lambda m: vals[m.group(1)], template)


def normalize_email(raw: str) -> str | None:
    try:
        return validate_email(raw.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError:
        return None


def split_addresses(text: str) -> list[dict]:
    return [{"email": t} for t in re.split(r"[\s,;]+", text) if t]
