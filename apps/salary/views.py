from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.urls import resolve
from django.views.generic.dates import MonthArchiveView
from django.views.generic.edit import FormView
from rolepermissions.mixins import HasPermissionsMixin

from apps.challenge.models.session import Session
from apps.salary.forms import TimesheetFormSet
from apps.salary.models import Timesheet


class MonthlyTimesheets(HasPermissionsMixin, MonthArchiveView, FormView):
    required_permission = "challenge_season_crud"
    date_field = "day"
    month_format = "%m"
    allow_empty = True
    allow_future = True
    template_name = "salary/month_timesheets.html"
    form_class = TimesheetFormSet

    def get_queryset(self):
        return (
            (
                Session.objects.values("day")
                .filter(
                    Q(qualifications__actor=self.selected_user)
                    | Q(qualifications__helpers=self.selected_user)
                    | Q(qualifications__leader=self.selected_user)
                )
                .annotate(
                    orga_count=Count("orga_id", distinct=True),
                    monitor_count=Count(
                        "qualifications__pk",
                        filter=Q(qualifications__helpers=self.selected_user)
                        | Q(qualifications__leader=self.selected_user),
                        distinct=True,
                    ),
                    intervenant_count=Count(
                        "qualifications__pk",
                        filter=Q(qualifications__actor=self.selected_user),
                        distinct=True,
                    ),
                )
            )
            .exclude(intervenant_count=0, monitor_count=0)
            .order_by("day")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_url"] = resolve(self.request.path).url_name
        context["formset"] = context["form"]
        return context

    def get_month(self):
        month = super().get_month()
        return month if month is not None else str(date.today().month)

    def get_year(self):
        year = super().get_year()
        return year if year is not None else str(date.today().year)

    def get_initial(self):
        initial = [
            {
                "user": self.selected_user,
                "date": session["day"],
                "time_monitor": session["monitor_count"] * 4
                + (0.5 * (session["orga_count"] - 1)),
                "time_actor": session["intervenant_count"] * 2,
                "overtime": Timesheet.objects.get(date=session["day"], user=self.selected_user).overtime,
                "traveltime": Timesheet.objects.get(date=session["day"], user=self.selected_user).traveltime,
            }
            for session in self.object_list
        ]
        return initial

    def get_success_url(self):
        return self.request.path

    def form_valid(self, formset):
        """If the form is valid, save the associated model."""
        for form in formset:
            form.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        self.date_list, self.object_list, extra_context = self.get_dated_items()
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        self.date_list, self.object_list, extra_context = self.get_dated_items()
        context = self.get_context_data(
            object_list=self.object_list,
            date_list=self.date_list,
            form=form,
            **extra_context
        )

        return self.render_to_response(context)


class MyMonthlyTimesheets(MonthlyTimesheets):
    def dispatch(self, request, *args, **kwargs):
        self.selected_user = get_user_model().objects.get(pk=67)
        return super().dispatch(request, *args, **kwargs)
