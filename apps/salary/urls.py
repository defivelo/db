from django.conf.urls import include, url
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from apps.salary.views import (
    CleanupOrphanedTimesheets,
    ExportMonthlyControl,
    ExportMonthlyTimesheets,
    RedirectUserMonthlyTimesheets,
    SendTimesheetsReminder,
    UserMonthlyTimesheets,
    ValidationsMonthView,
    ValidationsYearView,
    ValidationUpdate,
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
                                r"^cleanup/$",
                                CleanupOrphanedTimesheets.as_view(),
                                name="cleanup-timesheets",
                            ),
                            url(
                                r"(?P<format>[a-z]+)-export$",
                                ExportMonthlyTimesheets.as_view(),
                                name="accounting-export",
                            ),
                            url(
                                r"(?P<format>[a-z]+)-control$",
                                ExportMonthlyControl.as_view(),
                                name="control-export",
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
    # Validations
    url(
        r"^validations/(?P<year>[0-9]{4})/",
        include(
            [
                url(
                    r"^$",
                    never_cache(ValidationsYearView.as_view()),
                    name="validations-year",
                ),
                url(
                    r"^(?P<month>[0-9]{1,2})/",
                    include(
                        [
                            url(
                                r"^$",
                                never_cache(
                                    ValidationsMonthView.as_view(month_format="%m")
                                ),
                                name="validations-month",
                            ),
                            url(
                                r"^(?P<canton>[A-z]{2})/$",
                                never_cache(ValidationUpdate.as_view()),
                                name="validation-update",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
