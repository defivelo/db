from django.conf.urls import include
from django.urls import re_path, reverse_lazy
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
    re_path(
        r"^timesheets/",
        include(
            [
                re_path(
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
                re_path(
                    r"^(?P<year>\d{4})/$",
                    YearlyTimesheets.as_view(),
                    name="timesheets-overview",
                ),
                re_path(
                    r"^(?P<year>[0-9]{4})-(?P<month>[0-9]+)/",
                    include(
                        [
                            re_path(
                                r"^$",
                                RedirectUserMonthlyTimesheets.as_view(),
                                name="my-timesheets",
                            ),
                            re_path(
                                r"^cleanup/$",
                                CleanupOrphanedTimesheets.as_view(),
                                name="cleanup-timesheets",
                            ),
                            re_path(
                                r"(?P<format>[a-z]+)-export$",
                                ExportMonthlyTimesheets.as_view(),
                                name="accounting-export",
                            ),
                            re_path(
                                r"(?P<format>[a-z]+)-control$",
                                ExportMonthlyControl.as_view(),
                                name="control-export",
                            ),
                            re_path(
                                r"^(?P<pk>[0-9]+)/$",
                                UserMonthlyTimesheets.as_view(),
                                name="user-timesheets",
                            ),
                            re_path(
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
    re_path(
        r"^validations/(?P<year>[0-9]{4})/",
        include(
            [
                re_path(
                    r"^$",
                    never_cache(ValidationsYearView.as_view()),
                    name="validations-year",
                ),
                re_path(
                    r"^(?P<month>[0-9]{1,2})/",
                    include(
                        [
                            re_path(
                                r"^$",
                                never_cache(
                                    ValidationsMonthView.as_view(month_format="%m")
                                ),
                                name="validations-month",
                            ),
                            re_path(
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
