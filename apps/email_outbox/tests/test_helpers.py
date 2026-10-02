import datetime
from email import policy
from email.mime.image import MIMEImage
from email.parser import BytesParser
from types import SimpleNamespace

from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import Http404
from django.test import override_settings

import pytest

from apps.email_outbox import views

from .utils import CONSOLE, FILEBASED, LOCMEM, SEPARATOR, raw_message


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def parse(raw):
    return BytesParser(policy=policy.default).parsebytes(raw)


@pytest.mark.parametrize(
    "backend,supported", [(LOCMEM, True), (FILEBASED, True), (CONSOLE, False)]
)
def test_ensure_supported_backend(backend, supported):
    with override_settings(EMAIL_BACKEND=backend):
        if supported:
            views._ensure_supported_backend()
        else:
            with pytest.raises(Http404):
                views._ensure_supported_backend()


def test_get_email_file_basedir(tmp_path):
    with override_settings(EMAIL_FILE_PATH=str(tmp_path)):
        assert views._get_email_file_basedir() == str(tmp_path)
    with override_settings(EMAIL_FILE_PATH=str(tmp_path / "missing")):
        assert views._get_email_file_basedir() is None
    with override_settings(EMAIL_FILE_PATH=None):
        assert views._get_email_file_basedir() is None


def test_read_file_bytes(tmp_path):
    path = tmp_path / "mail.log"
    path.write_bytes(b"data")
    assert views._read_file_bytes(str(path)) == b"data"
    assert views._read_file_bytes(str(tmp_path / "missing")) is None


def test_split_aggregated_messages():
    assert views._split_aggregated_messages(b"one" + SEPARATOR + b"two") == [
        b"one",
        b"two",
    ]
    assert views._split_aggregated_messages(b"a\r\n" + b"-" * 50 + b" \r\nb") == [
        b"a",
        b"b",
    ]
    assert views._split_aggregated_messages(b"a\n" + b"-" * 49 + b"\nb") == [
        b"a\n" + b"-" * 49 + b"\nb"
    ]


def test_split_aggregated_messages_invalid_input():
    assert views._split_aggregated_messages("not bytes") == ["not bytes"]


def test_parse_raw_to_messages_skips_empty_chunks():
    raw = raw_message(subject="A") + SEPARATOR + b"  " + SEPARATOR
    messages = views._parse_raw_to_messages(raw + raw_message(subject="B"))
    assert [m["Subject"] for m in messages] == ["A", "B"]


def test_parse_date_header():
    assert views._parse_date_header(None) is None
    assert views._parse_date_header("garbage") is None
    assert views._parse_date_header("Tue, 01 Sep 2026 10:00:00 +0000") == (
        datetime.datetime(2026, 9, 1, 10, tzinfo=datetime.timezone.utc)
    )


def test_safe_dt():
    assert views._safe_dt(0) == datetime.datetime.fromtimestamp(0)
    assert views._safe_dt(1e20) is None


def test_compute_filebased_fingerprint(tmp_path):
    empty = views._compute_filebased_fingerprint(str(tmp_path))
    (tmp_path / "a.log").write_bytes(b"x")
    (tmp_path / "subdir").mkdir()
    assert views._compute_filebased_fingerprint(str(tmp_path)) != empty
    assert views._compute_filebased_fingerprint(str(tmp_path / "missing")) == "0"


def test_filebased_cache_key_is_stable():
    assert views._filebased_cache_key("/a") == views._filebased_cache_key("/a")
    assert views._filebased_cache_key("/a") != views._filebased_cache_key("/b")


def test_ensure_light_styles_in_head():
    html = views._ensure_light_styles('<html><head lang="fr"></head></html>')
    assert html.startswith('<html><head lang="fr"><style>')


def test_ensure_light_styles_before_body():
    html = views._ensure_light_styles("<BODY>hi</BODY>")
    assert html.startswith("<style>")
    assert html.endswith("<BODY>hi</BODY>")


def test_ensure_light_styles_wraps_fragment():
    html = views._ensure_light_styles("<p>hi</p>")
    assert html.startswith("<!DOCTYPE html><html><head>")
    assert html.endswith("<body><p>hi</p></body></html>")


def test_extract_html_body_prefers_html_alternative():
    em = EmailMessage(body="plain")
    em.alternatives = [("<i>x</i>", "text/x-other"), ("<b>html</b>", "text/html")]
    body, content_type = views._extract_html_body(em)
    assert content_type == "text/html"
    assert "<b>html</b>" in body
    assert "plain" not in body


def test_extract_html_body_escapes_plain_text():
    em = EmailMessage(body="a <b>\nb")
    body, content_type = views._extract_html_body(em)
    assert content_type == "text/html"
    assert "a &lt;b&gt;<br>b" in body
    assert "<style>" in body


def test_build_from_parsed_multipart():
    raw = raw_message(
        html="<p>html</p>",
        attachments=[("notes.txt", "some text", "text/plain")],
    )
    em = views._build_django_email_from_parsed(parse(raw), None)
    assert em.subject == "Hello"
    assert em.from_email == "sender@example.com"
    assert em.to == ["to@example.com"]
    assert em.cc == ["cc@example.com"]
    assert em.body.strip() == "Plain body"
    assert em.alternatives == [("<p>html</p>", "text/html")]
    assert em.sent_at is not None
    assert em.attachments_meta == [
        {"name": "notes.txt", "size": 9, "content_type": "text/plain"}
    ]
    assert em.attachments_data[0]["content"] == b"some text"


def test_build_from_parsed_binary_attachment():
    raw = raw_message(attachments=[("f.bin", b"\x00\x01", "application/pdf")])
    em = views._build_django_email_from_parsed(parse(raw), None)
    assert em.attachments_data == [
        {"name": "f.bin", "content": b"\x00\x01", "content_type": "application/pdf"}
    ]


def test_build_from_parsed_single_part_html():
    raw = (
        b"Subject: Html\nFrom: a@example.com\nTo: b@example.com\n"
        b"Content-Type: text/html; charset=utf-8\n\n<p>hi</p>\n"
    )
    em = views._build_django_email_from_parsed(parse(raw), None)
    assert em.body == ""
    assert em.alternatives == [("<p>hi</p>\n", "text/html")]
    assert em.attachments_meta == []


def test_build_from_parsed_single_part_text_without_date_uses_mtime(tmp_path):
    path = tmp_path / "mail.log"
    path.write_bytes(b"x")
    raw = b"Subject: Plain\nBcc: hidden@example.com\n\nbody\n"
    em = views._build_django_email_from_parsed(parse(raw), str(path))
    assert em.body == "body\n"
    assert em.bcc == ["hidden@example.com"]
    assert isinstance(em.sent_at, datetime.datetime)


def test_build_from_parsed_without_date_and_missing_path(tmp_path):
    raw = b"Subject: Plain\n\nbody\n"
    em = views._build_django_email_from_parsed(parse(raw), str(tmp_path / "nope"))
    assert em.sent_at is None


def test_build_from_parsed_unknown_charset_falls_back_to_utf8():
    raw = (
        b"Subject: Weird\nMIME-Version: 1.0\n"
        b'Content-Type: multipart/mixed; boundary="XX"\n\n'
        b"--XX\nContent-Type: text/plain; charset=x-unknown\n\nplain \xc3\xa9\n"
        b"--XX\nContent-Type: text/html; charset=x-unknown\n\n<p>html</p>\n"
        b"--XX\nContent-Type: text/plain; charset=x-unknown\n"
        b'Content-Disposition: attachment; filename="a.txt"\n\nattached\n'
        b"--XX--\n"
    )
    em = views._build_django_email_from_parsed(parse(raw), None)
    assert em.body == "plain é"
    assert em.alternatives == [("<p>html</p>", "text/html")]
    assert em.attachments_data[0]["name"] == "a.txt"
    assert em.attachments_data[0]["content"] == b"attached"


def test_build_from_parsed_single_part_unknown_charset():
    raw = b"Subject: Weird\nContent-Type: text/plain; charset=x-unknown\n\nhi\n"
    em = views._build_django_email_from_parsed(parse(raw), None)
    assert em.body == "hi\n"


def test_populate_attachments_from_locmem():
    em = EmailMessage()
    em.attachments = [
        ("a.txt", "text", "text/plain"),
        ("b.bin", b"\x00"),
        (None, None),
        MIMEImage(b"GIF89a", "gif"),
    ]
    views._populate_attachments_from_locmem(em)
    assert em.attachments_meta == [
        {"name": "a.txt", "size": 4, "content_type": "text/plain"},
        {"name": "b.bin", "size": 1, "content_type": "application/octet-stream"},
        {"name": "attachment", "size": 0, "content_type": "application/octet-stream"},
        {"name": "attachment", "size": 6, "content_type": "image/gif"},
    ]
    assert em.attachments_data[0]["content"] == b"text"
    assert em.attachments_data[3]["content"] == b"GIF89a"


def test_populate_attachments_from_locmem_skips_broken_attachment():
    class Broken:
        def get_filename(self):
            raise RuntimeError

    em = EmailMessage()
    em.attachments = [Broken()]
    views._populate_attachments_from_locmem(em)
    assert em.attachments_meta == []
    assert em.attachments_data == []


def test_populate_metadata_from_locmem_handles_message_failure():
    def broken():
        raise RuntimeError

    em = SimpleNamespace(message=broken, attachments=[])
    views._populate_metadata_from_locmem(em)
    assert em.sent_at is None
    assert em.attachments_meta == []


def test_populate_metadata_from_locmem_reads_date():
    em = EmailMessage(subject="s", body="b", to=["a@example.com"])
    views._populate_metadata_from_locmem(em)
    assert isinstance(em.sent_at, datetime.datetime)


def test_get_outbox_unsupported_backend_is_empty():
    with override_settings(EMAIL_BACKEND=CONSOLE):
        assert views._get_outbox() == []


def test_fetch_outbox_filebased_without_basedir(tmp_path):
    with override_settings(EMAIL_FILE_PATH=str(tmp_path / "missing")):
        assert views._fetch_outbox_filebased() == []
        assert views._get_filebased_index_cached() == []
        assert views._refresh_filebased_index() == []
        with pytest.raises(Http404):
            views._get_message_filebased_by_idx(0)
