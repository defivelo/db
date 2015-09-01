from django.conf.urls import url

from .views import UserDetail, UserUpdate

urlpatterns = [
    url(r'^edit/$', UserUpdate.as_view(), name="user-update"),
]
