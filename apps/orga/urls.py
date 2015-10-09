# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.cache import never_cache

from .views import (
    OrganizationCreateView, OrganizationDeleteView, OrganizationDetailView,
    OrganizationsListView, OrganizationUpdateView,
)

urlpatterns = [
    url(r'^$', never_cache(OrganizationsListView.as_view()),
        name="organization-list"),
    url(r'^new/$', OrganizationCreateView.as_view(),
        name="organization-create"),
    url(r'^(?P<pk>[0-9]+)/$', never_cache(OrganizationDetailView.as_view()),
        name="organization-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', OrganizationUpdateView.as_view(),
        name="organization-update"),
    url(r'^(?P<pk>[0-9]+)/delete/$', OrganizationDeleteView.as_view(),
        name="organization-delete"),
]
