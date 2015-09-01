from django.conf.urls import url

from .views import UserCreate, UserDetail, UserList, UserUpdate

urlpatterns = [
    url(r'^$', UserList.as_view(), name="user-list"),
    url(r'^new/$', UserCreate.as_view(), name="user-create"),
    url(r'^(?P<pk>[0-9]+)/$', UserDetail.as_view(), name="user-detail"),
    url(r'^(?P<pk>[0-9]+)/update/$', UserUpdate.as_view(), name="user-update"),
    url(r'^me/$', UserUpdate.as_view(), name="profile-update"),
]
