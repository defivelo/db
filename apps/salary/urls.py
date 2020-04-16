from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView

from apps.salary.views import (
    ExportMonthlyTimesheets,
    RedirectUserMonthlyTimesheets,
    SendTimesheetsReminder,
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
                    r"^$",
                    RedirectView.as_view(
                        url=reverse_lazy(
                            "salary:timesheets-overview",
                            kwargs={"year": timezone.now().year},
                        ),
                        permanent=False,
                    ),
                    name="timesheets",
                ),
                url(
                    r"^(?P<year>\d{4})/$",
                    YearlyTimesheets.as_view(),
                    name="timesheets-overview",
                ),
                url(
                    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]+)/",
                    include(
                        [
                            url(
                                r"^$",
                                RedirectUserMonthlyTimesheets.as_view(),
                                name="my-timesheets",
                            ),
                            url(
                                r"(?P<format>[a-z]+)-export$",
                                ExportMonthlyTimesheets.as_view(),
                                name="cresus-export",
                            ),
                            url(
                                r"^(?P<pk>[0-9]+)/$",
                                UserMonthlyTimesheets.as_view(),
                                name="user-timesheets",
                            ),
                            url(
                                r"^send_reminder/$",
                                SendTimesheetsReminder.as_view(),
                                name="send-timesheets-reminder",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
