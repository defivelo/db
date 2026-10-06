from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

import pytest

from apps.email_outbox import views

from .utils import (
    CONSOLE,
    FILEBASED,
    LOCMEM,
    SEPARATOR,
    build_message,
    raw_message,
    write_email_file,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def locmem():
    with override_settings(EMAIL_BACKEND=LOCMEM):
        mail.outbox = []
        yield mail.outbox


@pytest.fixture
def maildir(tmp_path):
    with override_settings(EMAIL_BACKEND=FILEBASED, EMAIL_FILE_PATH=str(tmp_path)):
        yield tmp_path


@pytest.fixture
def two_files(maildir):
    aggregated = (
        raw_message(subject="First")
        + SEPARATOR
        + raw_message(
            subject="Second",
            html="<p>Second html</p>",
            attachments=[("report.pdf", b"%PDF-1.4", "application/pdf")],
        )
    )
    first = write_email_file(maildir, "a.log", aggregated + SEPARATOR, 1000)
    second = write_email_file(maildir, "b.log", raw_message(subject="Third"), 2000)
    return first, second


def list_url(**params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return reverse("email-outbox-list") + (f"?{query}" if query else "")


def detail_url(idx):
    return reverse("email-outbox-detail", kwargs={"idx": idx})


def body_url(idx):
    return reverse("email-outbox-body", kwargs={"idx": idx})


def attachment_url(idx, aidx):
    return reverse("email-outbox-attachment", kwargs={"idx": idx, "aidx": aidx})


def subjects(response):
    return [e["subject"] for e in response.context["emails"]]


@pytest.mark.parametrize(
    "url",
    [list_url(), detail_url(0), body_url(0), attachment_url(0, 0)],
)
def test_unsupported_backend_returns_404(admin_client, url):
    with override_settings(EMAIL_BACKEND=CONSOLE):
        assert admin_client.get(url).status_code == 404


def test_requires_staff(client, locmem):
    response = client.get(list_url())
    assert response.status_code == 302


def test_list_empty(admin_client, locmem):
    response = admin_client.get(list_url())
    assert response.status_code == 200
    assert response.context["count"] == 0
    assert response.context["num_pages"] == 1
    assert b"E-mails" in response.content


def test_list_locmem_most_recent_first(admin_client, locmem):
    build_message(subject="Old").send()
    build_message(subject="New", attachments=[("a.txt", "x", "text/plain")]).send()
    response = admin_client.get(list_url())
    assert subjects(response) == ["New", "Old"]
    first = response.context["emails"][0]
    assert first["idx"] == 1
    assert first["to"] == ["to@example.com"]
    assert first["cc"] == ["cc@example.com"]
    assert first["bcc"] == ["bcc@example.com"]
    assert first["attachments_count"] == 1
    assert first["sent_at"] is not None


@pytest.mark.parametrize(
    "params,page,expected",
    [
        ({"p": 2, "per_page": 2}, 2, ["C", "B"]),
        ({"p": "x", "per_page": 2}, 1, ["E", "D"]),
        ({"p": 0, "per_page": 2}, 1, ["E", "D"]),
        ({"p": 99, "per_page": 2}, 3, ["A"]),
        ({"per_page": "x"}, 1, ["E", "D", "C", "B", "A"]),
    ],
)
def test_list_pagination(admin_client, locmem, params, page, expected):
    for subject in "ABCDE":
        build_message(subject=subject).send()
    response = admin_client.get(list_url(**params))
    assert response.context["page"] == page
    assert subjects(response) == expected


def test_list_pagination_context(admin_client, locmem):
    for subject in "ABCDE":
        build_message(subject=subject).send()
    response = admin_client.get(list_url(p=2, per_page=2))
    context = response.context
    assert context["num_pages"] == 3
    assert context["has_prev"] and context["has_next"]
    assert (context["prev_page"], context["next_page"]) == (1, 3)
    assert context["page_range"] == [1, 2, 3]


def test_detail_locmem(admin_client, locmem):
    build_message(subject="Hi", attachments=[("a.txt", "abc", "text/plain")]).send()
    response = admin_client.get(detail_url(0))
    assert response.status_code == 200
    assert response.context["subject"] == "Hi"
    assert response.context["idx"] == 0
    assert response.context["attachments"] == [
        {"aidx": 0, "name": "a.txt", "size": 3, "content_type": "text/plain"}
    ]
    assert attachment_url(0, 0).encode() in response.content


def test_detail_locmem_bad_index(admin_client, locmem):
    build_message().send()
    assert admin_client.get(detail_url(1)).status_code == 404


def test_body_locmem_html(admin_client, locmem):
    build_message(html="<html><head></head><body>Rich</body></html>").send()
    response = admin_client.get(body_url(0))
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    assert "X-Frame-Options" not in response
    assert b"<head><style>" in response.content
    assert b"Rich" in response.content


def test_body_locmem_plain(admin_client, locmem):
    build_message(body="Line 1\n<Line 2>").send()
    response = admin_client.get(body_url(0))
    assert b"Line 1<br>&lt;Line 2&gt;" in response.content


def test_attachment_locmem(admin_client, locmem):
    build_message(attachments=[("a.csv", "1,2", "text/csv")]).send()
    response = admin_client.get(attachment_url(0, 0))
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == 'attachment; filename="a.csv"'
    assert response.content == b"1,2"


def test_attachment_locmem_bad_index(admin_client, locmem):
    build_message().send()
    assert admin_client.get(attachment_url(0, 0)).status_code == 404


def test_attachment_defaults_for_missing_fields(admin_client, locmem, monkeypatch):
    em = build_message()
    em.attachments_data = [{}]
    monkeypatch.setattr(views, "_get_message", lambda idx: em)
    response = admin_client.get(attachment_url(0, 0))
    assert response["Content-Type"] == "application/octet-stream"
    assert response["Content-Disposition"] == 'attachment; filename="attachment"'
    assert response.content == b""


def test_list_filebased(admin_client, two_files):
    response = admin_client.get(list_url())
    assert response.status_code == 200
    assert subjects(response) == ["Third", "Second", "First"]
    assert response.context["emails"][1]["attachments_count"] == 1


def test_list_filebased_missing_dir(admin_client, tmp_path):
    with override_settings(
        EMAIL_BACKEND=FILEBASED, EMAIL_FILE_PATH=str(tmp_path / "missing")
    ):
        response = admin_client.get(list_url())
    assert response.context["count"] == 0


def test_list_filebased_skips_unreadable_files(admin_client, two_files, monkeypatch):
    first, unused_second = two_files
    read = views._read_file_bytes
    monkeypatch.setattr(
        views, "_read_file_bytes", lambda p: None if p == first else read(p)
    )
    assert subjects(admin_client.get(list_url())) == ["Third"]


def test_filebased_backend_written_file(admin_client, maildir):
    mail.get_connection().send_messages(
        [build_message(subject="One"), build_message(subject="Two")]
    )
    assert subjects(admin_client.get(list_url())) == ["Two", "One"]
    assert admin_client.get(detail_url(1)).context["subject"] == "Two"


@pytest.mark.parametrize("idx,subject", [(0, "First"), (1, "Second"), (2, "Third")])
def test_detail_filebased(admin_client, two_files, idx, subject):
    response = admin_client.get(detail_url(idx))
    assert response.status_code == 200
    assert response.context["subject"] == subject


def test_detail_filebased_attachments(admin_client, two_files):
    response = admin_client.get(detail_url(1))
    assert response.context["attachments"] == [
        {"aidx": 0, "name": "report.pdf", "size": 8, "content_type": "application/pdf"}
    ]


def test_detail_filebased_bad_index(admin_client, two_files):
    assert admin_client.get(detail_url(3)).status_code == 404


def test_detail_filebased_missing_dir(admin_client, tmp_path):
    with override_settings(
        EMAIL_BACKEND=FILEBASED, EMAIL_FILE_PATH=str(tmp_path / "missing")
    ):
        assert admin_client.get(detail_url(0)).status_code == 404


def test_body_filebased(admin_client, two_files):
    assert b"Second html" in admin_client.get(body_url(1)).content
    assert b"Plain body" in admin_client.get(body_url(0)).content


def test_attachment_filebased(admin_client, two_files):
    response = admin_client.get(attachment_url(1, 0))
    assert response["Content-Type"] == "application/pdf"
    assert response.content == b"%PDF-1.4"
    assert admin_client.get(attachment_url(1, 1)).status_code == 404


def test_filebased_index_is_cached(two_files, monkeypatch):
    first_index = views._get_filebased_index_cached()
    monkeypatch.setattr(views, "_collect_file_paths_sorted", lambda basedir: [])
    assert views._get_filebased_index_cached() == first_index
    assert len(first_index) == 3


def test_filebased_index_rebuilt_when_files_change(two_files, maildir):
    assert len(views._get_filebased_index_cached()) == 3
    write_email_file(maildir, "c.log", raw_message(subject="Fourth"), 3000)
    assert len(views._get_filebased_index_cached()) == 4


def test_filebased_index_empty_file(maildir):
    write_email_file(maildir, "empty.log", b"", 1000)
    assert views._get_filebased_index_cached() == [(str(maildir / "empty.log"), 0)]


def stale_index(maildir, index):
    basedir = str(maildir)
    cache.set(
        views._filebased_cache_key(basedir),
        {
            "fingerprint": views._compute_filebased_fingerprint(basedir),
            "index": index,
        },
    )


def test_stale_index_chunk_out_of_range_is_refreshed(admin_client, two_files, maildir):
    first, unused_second = two_files
    stale_index(maildir, [(first, 5)])
    response = admin_client.get(detail_url(0))
    assert response.context["subject"] == "First"


def test_stale_index_missing_file_is_refreshed(admin_client, two_files, maildir):
    stale_index(maildir, [(str(maildir / "gone.log"), 0)])
    response = admin_client.get(detail_url(0))
    assert response.context["subject"] == "First"


def test_stale_index_after_refresh_returns_404(
    admin_client, two_files, maildir, monkeypatch
):
    first, unused_second = two_files
    stale_index(maildir, [(first, 5)])
    monkeypatch.setattr(views, "_refresh_filebased_index", lambda: None)
    assert admin_client.get(detail_url(0)).status_code == 404


def test_get_message_falls_back_to_full_scan(admin_client, two_files, monkeypatch):
    def broken(idx):
        raise RuntimeError

    monkeypatch.setattr(views, "_get_message_filebased_by_idx", broken)
    assert admin_client.get(detail_url(2)).context["subject"] == "Third"
    assert admin_client.get(detail_url(3)).status_code == 404


def test_detail_filebased_empty_file(admin_client, maildir):
    write_email_file(maildir, "empty.log", b"", 1000)
    response = admin_client.get(detail_url(0))
    assert response.status_code == 200
    assert response.context["subject"] == ""


def test_filebased_index_rebuilt_when_cached_index_is_invalid(two_files, maildir):
    stale_index(maildir, ("not", "a list"))
    assert len(views._get_filebased_index_cached()) == 3


@pytest.mark.parametrize(
    "per_page,expected",
    [(0, 1), (-3, 1), (views.MAX_PER_PAGE + 1, views.MAX_PER_PAGE)],
)
def test_list_per_page_is_bounded(admin_client, locmem, per_page, expected):
    build_message().send()
    response = admin_client.get(list_url(per_page=per_page))
    assert response.status_code == 200
    assert response.context["per_page"] == expected


def test_filebased_index_skips_unreadable_files(two_files, monkeypatch):
    first, second = two_files
    read = views._read_file_bytes
    monkeypatch.setattr(
        views, "_read_file_bytes", lambda p: None if p == first else read(p)
    )
    assert views._get_filebased_index_cached() == [(second, 0)]
