# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from django.views.decorators.cache import never_cache

from .views import UserCreate, UserDetail, UserList, UserListExport, UserUpdate

urlpatterns = [
    url(r'^$', never_cache(UserList.as_view()), name="user-list"),
    url(r'^(?P<format>[a-z]+)export/$',
        never_cache(UserListExport.as_view()),
        name="user-list-export"),
    url(r'^new/$', UserCreate.as_view(), name="user-create"),
    url(r'^(?P<pk>[0-9]+)/$',
        never_cache(UserDetail.as_view()), name="user-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', UserUpdate.as_view(), name="user-update"),
    url(r'^me/$', UserUpdate.as_view(), name="profile-update"),
]
