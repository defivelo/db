from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import formats, timezone, translation
from django.utils.dates import MONTHS_3
from django.utils.translation import ugettext as u
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, TemplateView
from django.views.generic.dates import MonthArchiveView
from django.views.generic.edit import FormView

from tablib import Dataset

from apps.challenge.models.session import Session
from apps.common import DV_STATE_CHOICES
from apps.common.views import ExportMixin
from apps.salary.forms import ControlTimesheetFormSet, TimesheetFormSet
from apps.salary.models import Timesheet
from defivelo.roles import has_permission

from .. import timesheets_overview


class RedirectUserMonthlyTimesheets(RedirectView):
    is_permanent = False

    def get_redirect_url(self, *args, **kwargs):
        kwargs["pk"] = self.request.user.pk
        return reverse("salary:user-timesheets", kwargs=kwargs,)


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
                    leader_count=Count(
                        "qualifications__pk",
                        filter=Q(qualifications__leader=self.selected_user),
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
        context["year"] = self.get_year()
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
            form.initial.get("validated") for form in context["form"].forms
        )
        context["in_the_future"] = date.today() < context["month"]
        context["is_current_month"] = date.today().replace(day=1) == context["month"]
        all_sessions = (
            Session.objects.filter(
                Q(qualifications__actor=self.selected_user)
                | Q(qualifications__helpers=self.selected_user)
                | Q(qualifications__leader=self.selected_user)
            )
            .filter(day__in=[o["day"] for o in self.object_list])
            .prefetch_related("orga")
            .distinct()
        )
        context["all_sessions_by_day"] = {
            o["day"]: [s for s in all_sessions if s.day == o["day"]]
            for o in self.object_list
        }
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
                "actor_count": session["actor_count"],
                "leader_count": session["leader_count"],
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
        return reverse("salary:timesheets-overview", kwargs={"year": self.get_year()})

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
        self.selected_user = (
            get_object_or_404(
                timesheets_overview.get_visible_users(self.request.user),
                pk=self.kwargs["pk"],
            )
            if self.kwargs["pk"]
            else self.request.user
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
        context["canton"] = active_canton = self.request.GET.get("canton")

        users = timesheets_overview.get_visible_users(self.request.user).order_by(
            "first_name", "last_name"
        )
        global_timesheets_status_matrix = timesheets_overview.get_timesheets_status_matrix(
            year=year, users=users
        )
        if active_canton:
            users = users.filter(profile__affiliation_canton=active_canton)
            timesheets_status_matrix = timesheets_overview.get_timesheets_status_matrix(
                year=year, users=users
            )
        else:
            timesheets_status_matrix = global_timesheets_status_matrix

        context["months"] = MONTHS_3
        context["timesheets_status_matrix"] = timesheets_status_matrix
        context[
            "show_reminder_button_months"
        ] = timesheets_overview.get_missing_timesheet_status_per_month(
            global_timesheets_status_matrix
        )
        context[
            "timesheets_amount"
        ] = timesheets_overview.get_timesheets_amount_by_month(year=year, users=users)
        context["cantons"] = DV_STATE_CHOICES
        context["active_canton"] = (
            dict(DV_STATE_CHOICES)[active_canton] if active_canton else None
        )

        return context


class ExportMonthlyTimesheets(ExportMixin, MonthArchiveView):
    date_field = "date"
    month_format = "%m"
    allow_empty = False
    allow_future = False
    model = Timesheet

    def get_queryset(self):
        active_canton = self.request.GET.get("canton")
        users = timesheets_overview.get_visible_users(self.request.user).order_by(
            "first_name", "last_name"
        )
        if active_canton:
            users = users.filter(profile__affiliation_canton=active_canton)
        return super().get_queryset().filter(validated_at__isnull=False, user__in=users)

    def get_dataset_title(self):
        return _("Export Crésus {month} {year}").format(
            month=self.get_month(), year=self.get_year()
        )

    @property
    def export_filename(self):
        return "%s-%s-%s" % ("export-cresus", self.get_year(), self.get_month())

    def get_dataset(self, html=False):
        dataset = Dataset()
        dataset.append(
            [
                u("Nom"),
                u("Prénom"),
                u("Année courante"),
                u("Mois courant"),
                u("Numéro d'employé Crésus"),
                u("Salaire heure Formateur"),  # 0
                u("Salaire heures moniteur"),  # time_helper
                u("Prime moniteur 2"),  # leader_count
                u("Salaire heures supplémentaires"),  # overtime
                u("Salaire heures de trajet"),  # traveltime
                u("Salaire heure moniteur Finale"),  # not implented
                u("interventions"),  # actor_count
            ]
        )
        _, object_list, _ = self.get_dated_items()

        salary_details_list = (
            object_list.values("user")
            .annotate(
                cresus_employee_number=F("user__profile__cresus_employee_number"),
                user_id=F("user_id"),
                last_name=F("user__last_name"),
                first_name=F("user__first_name"),
                actor_count=Sum("actor_count"),
                leader_count=Sum("leader_count"),
                time_helper=Sum("time_helper"),
                traveltime=Sum("traveltime"),
                overtime=Sum("overtime"),
            )
            .order_by()
        )

        for salary_details in salary_details_list:
            dataset.append(
                [
                    salary_details["last_name"],
                    salary_details["first_name"],
                    self.get_year(),
                    self.get_month(),
                    salary_details["cresus_employee_number"],
                    0,
                    salary_details["time_helper"],
                    salary_details["leader_count"],
                    salary_details["overtime"],
                    salary_details["traveltime"],
                    0,
                    salary_details["actor_count"],
                ]
            )
        return dataset


class SendTimesheetsReminder(TemplateView):
    template_name = "salary/send_timesheets_reminder.html"
    required_permission = "timesheet_editor"

    def dispatch(self, request, *args, month, year, **kwargs):
        if not has_permission(request.user, self.required_permission):
            raise PermissionDenied
        self.month = int(month)
        self.year = int(year)
        users = (
            timesheets_overview.get_visible_users(self.request.user)
            .order_by("first_name", "last_name")
            .select_related("profile")
        )
        self.recipients = timesheets_overview.get_users_with_missing_timesheets(
            self.year, self.month, users
        )
        if not self.recipients:
            messages.warning(
                request,
                _("Aucun rappel à envoyer: les heures de ce mois sont déjà remplies."),
            )
            return redirect(self.get_redirect_url())
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self):
        return reverse("salary:timesheets-overview", kwargs={"year": self.year})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = self.get_redirect_url()
        context["recipients"] = self.recipients
        context["period"] = formats.date_format(date(self.year, self.month, 1), "F Y")
        email_subject, email_text, *_ = self.render_email_for_user(self.request.user)
        context["email_text"] = email_text
        context["email_subject"] = email_subject
        return context

    def post(self, request, *args, **kwargs):
        emails = [self.render_email_for_user(user) for user in self.recipients]
        mail.send_mass_mail(emails)
        messages.success(request, _("Rappel de soumission des heures expédié."))
        return redirect(self.get_redirect_url())

    def render_email_for_user(self, user):
        email_lang = user.profile.language or translation.get_language()
        with translation.override(email_lang):
            timesheets_url = self.request.build_absolute_uri(
                reverse(
                    "salary:my-timesheets",
                    kwargs={"year": self.year, "month": self.month},
                )
            )
            message = render_to_string(
                "salary/email_send_timesheets_reminder.txt",
                {
                    "profile": {"get_full_name": _("{Prénom} {Nom}")},
                    "current_site": Site.objects.get_current(),
                    "timesheets_url": timesheets_url,
                },
                self.request,
            )
            return (
                settings.EMAIL_SUBJECT_PREFIX + u("Soumission des heures"),
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
