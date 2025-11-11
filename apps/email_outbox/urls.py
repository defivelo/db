from django.contrib import admin
from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^outbox/$",
        admin.site.admin_view(views.outbox_list_view),
        name="email-outbox-list",
    ),
    re_path(
        r"^outbox/(?P<idx>\d+)/$",
        admin.site.admin_view(views.outbox_detail_view),
        name="email-outbox-detail",
    ),
    re_path(
        r"^outbox/(?P<idx>\d+)/body/$",
        admin.site.admin_view(views.outbox_body_view),
        name="email-outbox-body",
    ),
    re_path(
        r"^outbox/(?P<idx>\d+)/attachments/(?P<aidx>\d+)/$",
        admin.site.admin_view(views.outbox_attachment_view),
        name="email-outbox-attachment",
    ),
]
