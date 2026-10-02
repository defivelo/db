from django.template import Context, Template
from django.test import override_settings

import pytest

from apps.email_outbox.templatetags.outbox import is_supported_email_backend

from .utils import CONSOLE, FILEBASED, LOCMEM


@pytest.mark.parametrize(
    "backend,expected", [(LOCMEM, True), (FILEBASED, True), (CONSOLE, False)]
)
def test_is_supported_email_backend(backend, expected):
    with override_settings(EMAIL_BACKEND=backend):
        assert is_supported_email_backend() is expected


@pytest.mark.parametrize("backend,expected", [(LOCMEM, "True"), (CONSOLE, "False")])
def test_is_supported_email_backend_tag(backend, expected):
    template = Template(
        "{% load outbox %}{% is_supported_email_backend as ok %}{{ ok }}"
    )
    with override_settings(EMAIL_BACKEND=backend):
        assert template.render(Context()) == expected


@pytest.mark.django_db
def test_admin_shows_outbox_link_only_for_supported_backend(admin_client):
    with override_settings(EMAIL_BACKEND=LOCMEM):
        assert b"/admin/outbox/" in admin_client.get("/admin/").content
    with override_settings(EMAIL_BACKEND=CONSOLE):
        assert b"/admin/outbox/" not in admin_client.get("/admin/").content
