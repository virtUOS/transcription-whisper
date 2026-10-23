"""Keep API tokens out of the uvicorn logs.

Browsers can't set headers on a WebSocket upgrade, so API clients pass
`?token=tw_...` on /api/ws/status/{id}; uvicorn logs that path verbatim.
"""
import logging
import re

_TOKEN_RE = re.compile(r'(?<=[?&]token=)[^&\s"]+')


def _redact(value):
    return _TOKEN_RE.sub("REDACTED", value) if isinstance(value, str) else value


class TokenRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_redact(a) for a in record.args)
        return True


def install_token_redaction() -> None:
    """Add the filter to the loggers uvicorn writes request paths to (idempotent)."""
    for name in ("uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        if not any(isinstance(f, TokenRedactingFilter) for f in logger.filters):
            logger.addFilter(TokenRedactingFilter())
