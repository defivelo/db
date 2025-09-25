import math
import os
import re
from email import policy
from email.message import Message as PyEmailMessage
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib import admin
from django.core.mail import EmailMessage
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.html import conditional_escape
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt


def _ensure_supported_backend() -> None:
    if settings.EMAIL_BACKEND not in (
        "django.core.mail.backends.locmem.EmailBackend",
        "django.core.mail.backends.filebased.EmailBackend",
    ):
        raise Http404()


def _get_outbox() -> List[EmailMessage]:
    if settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend":
        from django.core import mail  # Imported lazily to ensure correct backend

        outbox: List[EmailMessage] = getattr(mail, "outbox", None)
        messages: List[EmailMessage] = []
        for em in outbox or []:
            _populate_metadata_from_locmem(em)
            messages.append(em)
        return messages
    elif settings.EMAIL_BACKEND == "django.core.mail.backends.filebased.EmailBackend":
        # Read .log/.eml files from EMAIL_FILE_PATH directory
        basedir = getattr(settings, "EMAIL_FILE_PATH", None)
        if not basedir or not os.path.isdir(basedir):
            return []
        # Collect latest files first
        filepaths: List[str] = [
            os.path.join(basedir, name)
            for name in os.listdir(basedir)
            if os.path.isfile(os.path.join(basedir, name))
        ]

        filepaths.sort(key=lambda p: os.path.getmtime(p))
        messages: List[EmailMessage] = []
        for path in filepaths:
            try:
                with open(path, "rb") as fh:
                    msg = BytesParser(policy=policy.default).parse(fh)
            except Exception:
                continue
            # Build a Django-like EmailMessage-ish wrapper
            subject = str(msg.get("Subject", ""))
            from_email = str(msg.get("From", ""))
            to = msg.get_all("To", []) or []
            cc = msg.get_all("Cc", []) or []
            bcc = msg.get_all("Bcc", []) or []
            sent_at = _parse_date_header(msg.get("Date"))
            if sent_at is None:
                try:
                    sent_at = _safe_dt(os.path.getmtime(path))
                except Exception:
                    sent_at = None

            # Convert to EmailMessage for re-use of rendering logic
            em = EmailMessage(subject=subject, body="", from_email=from_email, to=to)
            if cc:
                em.cc = cc
            if bcc:
                em.bcc = bcc
            em.sent_at = sent_at
            # Extract text/plain and text/html parts
            if msg.is_multipart():
                alts = []
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/html":
                        alts.append((part.get_content(), "text/html"))
                    elif ctype == "text/plain" and not em.body:
                        em.body = part.get_content()
                _populate_attachments_from_parsed(msg, em)
                if alts:
                    em.alternatives = alts
            else:
                ctype = msg.get_content_type()
                if ctype == "text/html":
                    em.body = ""
                    em.alternatives = [(msg.get_content(), "text/html")]
                else:
                    em.body = msg.get_content()
                _populate_attachments_from_parsed(msg, em)

            messages.append(em)
        return messages
    else:
        return []


def _get_message(idx: int) -> EmailMessage:
    outbox = _get_outbox()
    try:
        return outbox[idx]
    except (IndexError, TypeError):
        raise Http404()


def outbox_list_view(request: HttpRequest) -> HttpResponse:
    _ensure_supported_backend()
    emails = _get_outbox()
    # Order by descending original index (most recently added first)
    emails_sorted = sorted(enumerate(emails), key=lambda im: im[0], reverse=True)

    # Pagination
    try:
        page = int(request.GET.get("p", "1"))
    except ValueError:
        page = 1
    try:
        per_page = int(request.GET.get("per_page", "50"))
    except ValueError:
        per_page = 50
    count = len(emails_sorted)
    num_pages = max(1, math.ceil(count / per_page))
    if page < 1:
        page = 1
    if page > num_pages:
        page = num_pages
    start = (page - 1) * per_page
    end = start + per_page
    page_items = emails_sorted[start:end]

    # Build a view-model with safe defaults for template
    vm = [
        {
            "idx": orig_idx,
            "subject": m.subject or "",
            "from_email": m.from_email or "",
            "to": list(m.to or []),
            "cc": list(getattr(m, "cc", []) or []),
            "bcc": list(getattr(m, "bcc", []) or []),
            "sent_at": getattr(m, "sent_at", None),
            "attachments_count": len(getattr(m, "attachments_meta", []) or []),
        }
        for (orig_idx, m) in page_items
    ]

    # Compact page range around current page
    pr_start = max(1, page - 5)
    pr_end = min(num_pages, page + 5)
    page_range = list(range(pr_start, pr_end + 1))

    context = {
        "title": _("Emails"),
        "emails": vm,
        "page": page,
        "num_pages": num_pages,
        "has_prev": page > 1,
        "has_next": page < num_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
        "page_range": page_range,
        "count": count,
        "per_page": per_page,
    }
    context.update(admin.site.each_context(request))
    return render(request, "admin/outbox_list.html", context)


def outbox_detail_view(request: HttpRequest, idx: str) -> HttpResponse:
    _ensure_supported_backend()
    message = _get_message(int(idx))
    context = {
        "title": _("Email #%(num)s") % {"num": idx},
        "idx": int(idx),
        "subject": message.subject or "",
        "from_email": message.from_email or "",
        "to": list(message.to or []),
        "cc": list(getattr(message, "cc", []) or []),
        "bcc": list(getattr(message, "bcc", []) or []),
        "headers": getattr(message, "extra_headers", {}) or {},
        "sent_at": getattr(message, "sent_at", None),
        "attachments": [
            {"aidx": i, **meta}
            for i, meta in enumerate(getattr(message, "attachments_meta", []) or [])
        ],
    }
    context.update(admin.site.each_context(request))
    return render(request, "admin/outbox_detail.html", context)


def _extract_html_body(message: EmailMessage) -> Tuple[str, str]:
    # Returns (body_html, content_type)
    # Prefer HTML alternative if present (EmailMultiAlternatives)
    alternatives = getattr(message, "alternatives", None)
    if alternatives:
        for content, mime in alternatives:
            if mime == "text/html":
                return _ensure_light_styles(content), "text/html"
    # Fallback to plain text body
    text_body = message.body or ""
    # Some backends/log exports add a trailing separator line of many dashes
    text_body = _strip_trailing_separator(text_body)
    escaped = conditional_escape(text_body).replace("\n", "<br>")
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        "<body>{}</body></html>".format(escaped)
    )
    html = _ensure_light_styles(html)
    return html, "text/html"


def _ensure_light_styles(html: str) -> str:
    """Inject minimal CSS to force a light background and readable text.

    Attempts to add a <style> block either inside <head>, or right before <body>,
    or wraps the content if no standard structure is found.
    """
    style = (
        "<style>html,body{background:#fff !important;color:#000 !important;}"
        "a{color:#0645ad}img{max-width:100%;height:auto}</style>"
    )

    # Insert into <head> if present
    if re.search(r"<head[^>]*>", html, flags=re.IGNORECASE):
        return re.sub(
            r"(<head[^>]*>)", r"\1" + style, html, count=1, flags=re.IGNORECASE
        )

    # Else, insert immediately before <body>
    if re.search(r"<body[^>]*>", html, flags=re.IGNORECASE):
        return re.sub(
            r"(<body[^>]*>)", style + r"\1", html, count=1, flags=re.IGNORECASE
        )

    # Else, wrap content
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">' + style + "</head>"
        "<body>" + html + "</body></html>"
    )


def _strip_trailing_separator(text: str) -> str:
    """Remove a trailing separator line (>=50 consecutive dashes) at end of body.

    This safely keeps legitimate content that may contain small dash runs,
    and only strips if such a line appears at the very end.
    """
    try:
        import re as _re

        return _re.sub(r"(?:\r?\n)?-{50,}\s*$", "", text)
    except Exception:
        return text


@xframe_options_exempt
def outbox_body_view(request: HttpRequest, idx: str) -> HttpResponse:
    _ensure_supported_backend()
    message = _get_message(int(idx))
    body, content_type = _extract_html_body(message)
    return HttpResponse(body, content_type=content_type)


def outbox_attachment_view(request: HttpRequest, idx: str, aidx: str) -> HttpResponse:
    _ensure_supported_backend()
    message = _get_message(int(idx))
    attachments: List[Dict[str, Any]] = getattr(message, "attachments_data", []) or []
    try:
        att = attachments[int(aidx)]
    except (IndexError, ValueError, TypeError):
        raise Http404()
    filename = att.get("name") or "attachment"
    content = att.get("content") or b""
    content_type = att.get("content_type") or "application/octet-stream"
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = 'attachment; filename="%s"' % filename
    return response


def _populate_metadata_from_locmem(em: EmailMessage) -> None:
    # Attempt to extract Date header from generated message
    try:
        py_msg: PyEmailMessage = em.message()
        sent_at = _parse_date_header(py_msg.get("Date"))
    except Exception:
        sent_at = None
    em.sent_at = sent_at
    _populate_attachments_from_locmem(em)


def _populate_attachments_from_locmem(em: EmailMessage) -> None:
    meta: List[Dict[str, Any]] = []
    data: List[Dict[str, Any]] = []
    for att in getattr(em, "attachments", []) or []:
        if isinstance(att, tuple) and len(att) in (2, 3):
            # (filename, content[, mimetype])
            name = att[0] or "attachment"
            content = att[1]
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            else:
                content_bytes = content or b""
            ctype = att[2] if len(att) == 3 else "application/octet-stream"
            meta.append(
                {"name": name, "size": len(content_bytes), "content_type": ctype}
            )
            data.append({"name": name, "content": content_bytes, "content_type": ctype})
        else:
            # MIMEBase-like
            try:
                name = getattr(att, "get_filename", lambda: None)() or "attachment"
                ctype = getattr(
                    att, "get_content_type", lambda: "application/octet-stream"
                )()
                payload = getattr(att, "get_payload", lambda decode=True: b"")(
                    decode=True
                )
                content_bytes = payload or b""
                meta.append(
                    {"name": name, "size": len(content_bytes), "content_type": ctype}
                )
                data.append(
                    {"name": name, "content": content_bytes, "content_type": ctype}
                )
            except Exception:
                continue
    em.attachments_meta = meta
    em.attachments_data = data


def _populate_attachments_from_parsed(msg: PyEmailMessage, em: EmailMessage) -> None:
    meta: List[Dict[str, Any]] = []
    data: List[Dict[str, Any]] = []
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp or (part.get_filename()):
                name = part.get_filename() or "attachment"
                ctype = part.get_content_type() or "application/octet-stream"
                try:
                    content_bytes = part.get_content()
                    if isinstance(content_bytes, str):
                        content_bytes = content_bytes.encode("utf-8")
                except Exception:
                    try:
                        content_bytes = part.get_payload(decode=True) or b""
                    except Exception:
                        content_bytes = b""
                meta.append(
                    {"name": name, "size": len(content_bytes), "content_type": ctype}
                )
                data.append(
                    {"name": name, "content": content_bytes, "content_type": ctype}
                )
    else:
        # Single-part message isn't an attachment container
        pass
    em.attachments_meta = meta
    em.attachments_data = data


def _parse_date_header(date_value: Optional[str]):
    if not date_value:
        return None
    try:
        return parsedate_to_datetime(str(date_value))
    except Exception:
        return None


def _safe_dt(timestamp: float):
    try:
        import datetime as _dt

        return _dt.datetime.fromtimestamp(timestamp)
    except Exception:
        return None
