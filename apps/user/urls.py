from django.conf.urls import url

from .views import UserList, UserUpdate

urlpatterns = [
    url(r'^$', UserList.as_view(), name="user-list"),
    url(r'^me/$', UserUpdate.as_view(), name="profile-update"),
]
