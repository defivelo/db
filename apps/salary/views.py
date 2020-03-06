from datetime import date

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS_3
from django.views.generic import TemplateView
from django.views.generic.dates import MonthArchiveView
from django.views.generic.edit import FormView

from apps.challenge.models.session import Session
from apps.common import DV_STATE_CHOICES
from apps.salary.forms import ControlTimesheetFormSet, TimesheetFormSet
from apps.salary.models import Timesheet
from defivelo.roles import has_permission

from . import timesheets_overview


class UserMonthlyTimesheets(MonthArchiveView, FormView):
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
        context["menu_category"] = ["timesheet"]
        context["monitor_name"] = self.selected_user.get_full_name()
        namespaces = self.request.resolver_match.namespaces
        url_name = self.request.resolver_match.url_name
        context["prev_url"] = reverse(
            ":".join([*namespaces, url_name]),
            kwargs={
                "month": context["previous_month"].month,
                "year": context["previous_month"].year,
                "pk": self.selected_user.id,
            },
        )

        context["next_url"] = reverse(
            ":".join([*namespaces, url_name]),
            kwargs={
                "month": context["next_month"].month,
                "year": context["next_month"].year,
                "pk": self.selected_user.id,
            },
        )
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
                "user": self.selected_user,
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
        kwargs["form_kwargs"] = {"validator": self.request.user}
        return kwargs

    def get_success_url(self):
        return reverse("salary:timesheets-overview", kwargs={"year": self.get_year()})
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

    def dispatch(self, request, *args, **kwargs):
        self.selected_user = get_object_or_404(
            timesheets_overview.get_visible_users(self.request.user),
            pk=self.kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if has_permission(self.request.user, "timesheet_editor"):
            return ControlTimesheetFormSet
        else:
            return TimesheetFormSet


class YearlyTimesheets(TemplateView):
    template_name = "salary/timesheets_yearly_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_category"] = ["timesheet"]

        year = self.kwargs["year"]
        active_canton = self.request.GET.get("canton")

        users = timesheets_overview.get_visible_users(self.request.user).order_by(
            "first_name", "last_name"
        )
        if active_canton:
            users = users.filter(profile__affiliation_canton=active_canton)

        context["months"] = MONTHS_3
        context[
            "timesheets_status_matrix"
        ] = timesheets_overview.get_timesheets_status_matrix(year=year, users=users)
        context[
            "timesheets_amount"
        ] = timesheets_overview.get_timesheets_amount_by_month(year=year, users=users)
        context["cantons"] = DV_STATE_CHOICES
        context["active_canton"] = (
            dict(DV_STATE_CHOICES)[active_canton] if active_canton else None
        )

        return context
