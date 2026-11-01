"""Development email backend: prints emails to the terminal in readable form."""

from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

SHOWN_HEADERS = ("From", "To", "Cc", "Bcc", "Reply-To", "Subject", "Date")


class ReadableConsoleEmailBackend(ConsoleEmailBackend):
    """Like Django's console backend, but prints the body decoded.

    Django's console backend prints the raw encoded message, which wraps long lines
    with quoted-printable `=` breaks. That splits password-reset links so they
    can't be copied from the terminal.
    """

    def write_message(self, message):
        msg = message.message()
        for name in SHOWN_HEADERS:
            if msg[name]:
                self.stream.write(f"{name}: {msg[name]}\n")
        self.stream.write("\n")
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                charset = part.get_content_charset() or "utf-8"
                self.stream.write(part.get_payload(decode=True).decode(charset))
        self.stream.write("\n" + "-" * 79 + "\n")
