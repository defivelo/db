from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic.dates import MonthArchiveView
from django.views.generic.edit import FormView

from rolepermissions.mixins import HasPermissionsMixin

from apps.challenge.models.session import Session
from apps.salary.forms import ControlTimesheetFormSet, TimesheetFormSet
from apps.salary.models import Timesheet


class MonthlyTimesheets(MonthArchiveView, FormView):
    date_field = "day"
    month_format = "%m"
    allow_empty = True
    allow_future = True
    template_name = "salary/month_timesheets.html"

    def get_queryset(self):
        return (
            (
                Session.objects.values("day")
                .filter(
                    Q(qualifications__actor=self.selected_user)
                    | Q(qualifications__helpers=self.selected_user)
                    | Q(qualifications__leader=self.selected_user)
                )
                .filter(day__lte=timezone.now())
                .annotate(
                    orga_count=Count("orga_id", distinct=True),
                    helper_count=Count(
                        "qualifications__pk",
                        filter=Q(qualifications__helpers=self.selected_user)
                        | Q(qualifications__leader=self.selected_user),
                        distinct=True,
                    ),
                    actor_count=Count(
                        "qualifications__pk",
                        filter=Q(qualifications__actor=self.selected_user),
                        distinct=True,
                    ),
                )
            )
            .exclude(actor_count=0, helper_count=0)
            .order_by("day")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_category"] = "timesheet"
        context["nav_url"] = self.request.resolver_match.url_name
        context["formset"] = context["form"]
        context["fields_grouped_by_field_name"] = (
            {
                fieldname.label: [
                    form[fieldname.name] for form in context["form"].forms
                ]
                for fieldname in context["form"].forms[0].visible_fields()
            }
            if context["form"].forms
            else {}
        )
        context["can_print"] = all(
            form.initial["validated"] for form in context["form"].forms
        )
        context["in_the_future"] = date.today() < context["month"]
        context["is_current_month"] = date.today().replace(day=1) == context["month"]
        return context

    def get_month(self):
        return super().get_month() or date.today().month

    def get_year(self):
        return super().get_year() or date.today().year

    def get_initial(self):
        initial = []
        timesheets = {
            timesheet.date: timesheet
            for timesheet in Timesheet.objects.filter(
                date__in=[obj["day"] for obj in self.object_list],
                user=self.selected_user,
            )
        }
        for session in self.object_list:
            timesheet = timesheets.get(session["day"])
            attributes = {
                "date": session["day"],
                "time_helper": session["helper_count"]
                * (
                    4
                    if session["orga_count"] == 1 and session["helper_count"] > 1
                    else 4.5
                ),
                "time_actor": session["actor_count"],
                "overtime": timesheet.overtime if timesheet else 0,
                "traveltime": timesheet.traveltime if timesheet else 0,
                "validated": bool(timesheet.validated_at) if timesheet else False,
                "comments": timesheet.comments if timesheet else "",
            }
            initial.append(attributes)
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {
            "validator": self.request.user,
            "selected_user": self.selected_user,
        }
        return kwargs

    def get_success_url(self):
        return self.request.get_full_path()

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
            **extra_context,
        )
        return self.render_to_response(context)


class MyMonthlyTimesheets(MonthlyTimesheets):
    form_class = TimesheetFormSet

    def dispatch(self, request, *args, **kwargs):
        self.selected_user = request.user
        return super().dispatch(request, *args, **kwargs)


class UserMonthlyTimesheets(HasPermissionsMixin, MonthlyTimesheets):
    form_class = ControlTimesheetFormSet
    required_permission = "timesheet_editor"

    def dispatch(self, request, *args, **kwargs):
        self.selected_user = get_object_or_404(
            get_user_model().objects, pk=self.kwargs["pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["monitor_name"] = self.selected_user.get_full_name()
        context["prev_url"] = reverse(
            self.request.resolver_match.url_name,
            kwargs={
                "month": context["previous_month"].month,
                "year": context["previous_month"].year,
                "pk": self.selected_user.id,
            },
        )
        context["next_url"] = reverse(
            self.request.resolver_match.url_name,
            kwargs={
                "month": context["next_month"].month,
                "year": context["next_month"].year,
                "pk": self.selected_user.id,
            },
        )
        return context
