from django.conf.urls import include, url

from apps.salary.views import MyMonthlyTimesheets

urlpatterns = [
    url(
        r"^timesheets/(?:(?P<year>[0-9]{4})-(?P<month>[0-9]+)/)?",
        include([url(r"^me/$", MyMonthlyTimesheets.as_view(), name="my-timesheets"),]),
    ),
]
