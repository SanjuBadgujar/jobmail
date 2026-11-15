import logging
import re

_SENSITIVE = re.compile(r"(ya29\.[\w\-.]+|1//[\w\-.]+|(?i:token|secret)=\S+)")


class RedactFilter(logging.Filter):
    """Strip OAuth tokens/secrets from log output."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _SENSITIVE.sub("[REDACTED]", str(record.msg))
        return True


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RedactFilter())
