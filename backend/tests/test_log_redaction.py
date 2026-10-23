import logging

from uvicorn.logging import AccessFormatter

from app.log_redaction import install_token_redaction, TokenRedactingFilter


def _record(msg, args):
    return logging.LogRecord("uvicorn", logging.INFO, __file__, 1, msg, args, None)


def test_access_log_redacted():
    record = _record(
        '%s - "%s %s HTTP/%s" %d',
        ("1.2.3.4:5", "GET", "/api/ws/status/x?token=tw_abc&y=1", "1.1", 101),
    )
    TokenRedactingFilter().filter(record)
    out = AccessFormatter('%(client_addr)s - "%(request_line)s" %(status_code)s').format(record)
    assert "token=REDACTED&y=1" in out
    assert "tw_abc" not in out


def test_ws_accepted_line_redacted():
    record = _record(
        '%s - "WebSocket %s" [accepted]',
        (("1.2.3.4", 5), "/api/ws/status/x?token=tw_abc"),
    )
    assert TokenRedactingFilter().filter(record) is True
    assert "tw_abc" not in record.getMessage()
    assert "token=REDACTED" in record.getMessage()


def test_install_is_idempotent():
    install_token_redaction()
    install_token_redaction()
    for name in ("uvicorn.access", "uvicorn.error"):
        filters = [f for f in logging.getLogger(name).filters if isinstance(f, TokenRedactingFilter)]
        assert len(filters) == 1
