import os

from django.core.mail import EmailMultiAlternatives

LOCMEM = "django.core.mail.backends.locmem.EmailBackend"
FILEBASED = "django.core.mail.backends.filebased.EmailBackend"
CONSOLE = "django.core.mail.backends.console.EmailBackend"

SEPARATOR = b"\n" + b"-" * 79 + b"\n"


def build_message(subject="Hello", body="Plain body", html=None, attachments=()):
    em = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email="sender@example.com",
        to=["to@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
    )
    if html:
        em.attach_alternative(html, "text/html")
    for attachment in attachments:
        em.attach(*attachment)
    return em


def raw_message(**kwargs):
    return build_message(**kwargs).message().as_bytes()


def write_email_file(directory, name, content, mtime):
    path = os.path.join(str(directory), name)
    with open(path, "wb") as fh:
        fh.write(content)
    os.utime(path, (mtime, mtime))
    return path
