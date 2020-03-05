from django.conf.urls import include, url

from apps.salary.views import (
    MyMonthlyTimesheets,
    UserMonthlyTimesheets,
    YearlyTimesheets,
)

app_name = "salary"

urlpatterns = [
    url(
        r"^timesheets/",
        include(
            [
                url(
                    r"^(?P<year>\d{4})/$",
                    YearlyTimesheets.as_view(),
                    name="timesheets-overview",
                ),
                url(
                    r"^(?:(?P<year>[0-9]{4})-(?P<month>[0-9]+))?/",
                    include(
                        [
                            url(
                                r"^me/$",
                                MyMonthlyTimesheets.as_view(),
                                name="my-timesheets",
                            ),
                            url(
                                r"^(?P<pk>[0-9]+)/$",
                                UserMonthlyTimesheets.as_view(),
                                name="user-timesheets",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
