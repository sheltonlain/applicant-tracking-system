import io

from django.core.mail import EmailMessage

from config.email import ReadableConsoleEmailBackend


def test_console_email_prints_long_links_on_one_line():
    """Reset links must be copyable from the terminal (no quoted-printable `=` line breaks)."""
    link = "http://127.0.0.1:8000/accounts/reset/Mw/dhd9bl-40bb9119b3a7d3983df047eeeec2cb53/"
    stream = io.StringIO()
    backend = ReadableConsoleEmailBackend(stream=stream)

    sent = backend.send_messages(
        [EmailMessage("Reset your ATS password", f"Open this link:\n\n{link}\n", to=["a@b.com"])]
    )

    output = stream.getvalue()
    assert sent == 1
    assert link in output.splitlines()
    assert "Subject: Reset your ATS password" in output
    assert "To: a@b.com" in output
