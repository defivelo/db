# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import quote

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError, PermissionDenied
from django.template.defaultfilters import date, time
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_text
from django.utils.html import urlencode
from django.utils.translation import ugettext as u
from django.utils.translation import ugettext_lazy as _
from django.views.generic.dates import WeekArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from tablib import Dataset

from apps.common.views import ExportMixin
from defivelo.roles import has_permission, user_cantons
from defivelo.templatetags.dv_filters import lettercounter
from defivelo.views import MenuView

from ..forms import QualificationFormQuick, SessionForm
from ..models import Session
from ..models.qualification import (
    CATEGORY_CHOICE_A,
    CATEGORY_CHOICE_B,
    CATEGORY_CHOICE_C,
)
from .mixins import CantonSeasonFormMixin

EXPORT_NAMETEL = u("{name} - {tel}")


class SessionMixin(CantonSeasonFormMixin, MenuView):
    required_permission = "challenge_session_crud"
    model = Session
    context_object_name = "session"
    form_class = SessionForm
    raise_without_cantons = False

    def get_queryset(self):
        qs = super().get_queryset()
        try:
            return qs.filter(orga__address_canton__in=self.season_object.cantons)
        except FieldError:
            # For the cases qs is Qualification, not Session
            return qs

    def get_success_url(self):
        return reverse_lazy(
            "session-detail", kwargs={"seasonpk": self.season.pk, "pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super(SessionMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "season"
        context["season"] = self.season_object
        try:
            mysession = self.get_object()
        except AttributeError:
            return context

        session_pages = {
            "session_current": None,
            "session_next": None,
        }

        try:
            sessions = self.season.sessions_by_orga.filter(orga=mysession.orga)
        except AttributeError:
            sessions = []

        # Iterate through all of them, index is 'next'
        for session in sessions:
            session_pages["session_current"] = session_pages["session_next"]
            session_pages["session_next"] = session
            # On arrive
            if session_pages["session_next"].pk == mysession.pk:
                context["session_previous"] = session_pages["session_current"]
            # On y est
            if (
                session_pages["session_current"]
                and session_pages["session_current"].pk == mysession.pk
            ):
                context["session_next"] = session_pages["session_next"]
                break
        return context


class SessionsListView(SessionMixin, WeekArchiveView):
    date_field = "day"
    context_object_name = "sessions"
    allow_empty = True
    allow_future = True
    week_format = "%W"
    ordering = ["day", "begin", "duration"]

    def dispatch(self, request, *args, **kwargs):
        """
        Check allowances for access to list
        """
        allowed = False

        if has_permission(request.user, self.required_permission):
            # StateManagers
            # Check that the intersection isn't empty
            usercantons = user_cantons(request.user)
            if usercantons:
                if list(set(usercantons).intersection(set(self.season_object.cantons))):
                    # StateManager cantons
                    allowed = True
                else:
                    # If the user is marked as state manager for that season
                    if self.season_object.leader == self.request.user:
                        allowed = True
                    # Verify that this state manager can access that canton as mobile
                    elif list(
                        set(
                            [request.user.profile.affiliation_canton]
                            + request.user.profile.activity_cantons
                        ).intersection(set(self.season_object.cantons))
                    ):
                        allowed = True
        elif self.season_object.unprivileged_user_can_see(request.user):
            allowed = True

        if allowed:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class SessionDetailView(SessionMixin, DetailView):
    # Allow season fetch even for non-state managers
    allow_season_fetch = True

    def get_context_data(self, **kwargs):
        context = super(SessionDetailView, self).get_context_data(**kwargs)
        try:
            mysession = self.get_object()
        except AttributeError:
            return context
        context["quali_form_quick"] = QualificationFormQuick(
            {
                "session": mysession,
                "name": _("Classe %s") % lettercounter(mysession.n_qualifications + 1),
            }
        )
        # Build a meaningful mailto: link towards all session available emails, with meaningful subject and body.
        session_helpers = [
            f"{s.helper.get_full_name()} <{s.helper.email}>"
            for s in mysession.chosen_staff.order_by(
                "helper__first_name", "helper__last_name"
            )
        ]
        context["session_mailtoall"] = None
        if session_helpers:
            emailparts = {
                "subject": (
                    settings.EMAIL_SUBJECT_PREFIX
                    + _("Qualifs {session}").format(session=mysession)
                ),
                "body": render_to_string(
                    "challenge/session_email_to_helpers.txt",
                    {
                        "current_site": Site.objects.get_current(),
                        "session": mysession,
                        "session_url": self.request.build_absolute_uri(
                            reverse(
                                "session-detail",
                                kwargs={
                                    "seasonpk": mysession.season.pk,
                                    "pk": mysession.pk,
                                },
                            )
                        ),
                    },
                ),
            }
            context["session_mailtoall"] = "mailto:{emaillist}?{options}".format(
                emaillist=", ".join(session_helpers),
                options=urlencode(emailparts, quote_via=quote),
            )

        return context

    def get_queryset(self):
        return (
            super(SessionDetailView, self)
            .get_queryset()
            .prefetch_related(
                "orga",
                "qualifications",
                "qualifications__leader",
                "qualifications__leader__profile",
                "qualifications__helpers",
                "qualifications__helpers__profile",
                "qualifications__actor",
                "qualifications__actor__profile",
                "qualifications__activity_A",
                "qualifications__activity_B",
                "qualifications__activity_C",
            )
        )

    def dispatch(self, request, *args, **kwargs):
        """
        Check allowances for access to view
        """
        allowed = False

        if has_permission(request.user, self.required_permission):
            allowed = True
        else:
            try:
                list_or_single_session_visible = self.get_object().visible
            except AttributeError:
                list_or_single_session_visible = True

            # Read-only view when session is visible
            if (
                self.season
                and self.season.unprivileged_user_can_see(request.user)
                and list_or_single_session_visible
            ):
                allowed = True

        if allowed:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class SessionUpdateView(SessionMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Session mise à jour")

    def dispatch(self, request, *args, **kwargs):
        """
        Check allowances for access to updateview
        """
        allowed = False

        if (
            has_permission(request.user, self.required_permission)
            and self.season
            and self.season.manager_can_crud
        ):
            # StateManager, and it's the right moment
            allowed = True
        elif (
            self.get_object().orga.coordinator == request.user
            and self.season_object.coordinator_can_update
        ):
            # Coordinator, and it's the right moment
            allowed = True

        if allowed:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class SessionCreateView(SessionMixin, SuccessMessageMixin, CreateView):
    success_message = _("Session créée")

    def dispatch(self, request, *args, **kwargs):
        """
        Check allowances for access to view
        """
        allowed = False

        if has_permission(request.user, self.required_permission):
            if self.season and self.season.manager_can_crud:
                allowed = True

        if allowed:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class SessionDeleteView(SessionMixin, SuccessMessageMixin, DeleteView):
    success_message = _("Session supprimée")

    def dispatch(self, request, *args, **kwargs):
        """
        Check allowances for access to view
        """
        allowed = False

        if has_permission(request.user, self.required_permission):
            if self.season and self.season.manager_can_crud:
                allowed = True

        if allowed:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        self.get_object().get_related_timesheets().delete()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("season-detail", kwargs={"pk": self.kwargs["seasonpk"]})


class SessionStaffChoiceView(SessionDetailView):
    template_name = "challenge/session_availability.html"


class SessionExportView(ExportMixin, SessionMixin, DetailView):
    # Allow season fetch even for non-state managers
    allow_season_fetch = True

    @property
    def export_filename(self):
        return _("Session") + "-" + force_text(self.object)

    def get_dataset(self):
        dataset = Dataset()
        # Prépare le fichier
        dataset.append_col(
            [
                u("Date"),
                u("Canton"),
                u("Établissement"),
                u("Emplacement"),
                u("Heures"),
                u("Nombre de qualifs"),
                # Logistique
                u("Moniteur + / Photographe"),
                u("Mauvais temps"),
                u("Logistique vélos"),
                u("N° de contact vélos"),
                u("Pommes"),
                u("Total vélos"),
                u("Total casques"),
                u("Remarques"),
                # Qualif
                u("Classe"),
                u("Enseignant"),
                u("Moniteur 2"),
                u("Moniteur 1"),
                u("Moniteur 1"),
                u("Nombre d’élèves"),
                u("Nombre de vélos"),
                u("Nombre de casques"),
                CATEGORY_CHOICE_A,
                CATEGORY_CHOICE_B,
                CATEGORY_CHOICE_C,
                u("Intervenant"),
                u("Remarques"),
            ]
        )
        session = self.object
        session_place = session.place
        if not session_place:
            session_place = (
                session.address_city
                if session.address_city
                else session.orga.address_city
            )
        col = [
            date(session.day),
            session.orga.address_canton,
            session.orga.name,
            session_place,
            "%s - %s" % (time(session.begin), time(session.end)),
            session.n_qualifications,
            EXPORT_NAMETEL.format(
                name=session.superleader.get_full_name(),
                tel=session.superleader.profile.natel,
            )
            if session.superleader
            else "",
            str(session.fallback),
            session.bikes_concept,
            session.bikes_phone,
            session.apples,
            session.n_bikes,
            session.n_helmets,
            session.comments,
        ]
        if session.n_qualifications:
            for quali in session.qualifications.all():
                if not len(col):
                    col = [""] * 14
                col.append(quali.name)
                col.append(
                    EXPORT_NAMETEL.format(
                        name=quali.class_teacher_fullname, tel=quali.class_teacher_natel
                    )
                    if quali.class_teacher_fullname
                    else ""
                )
                col.append(
                    EXPORT_NAMETEL.format(
                        name=quali.leader.get_full_name(),
                        tel=quali.leader.profile.natel,
                    )
                    if quali.leader
                    else ""
                )
                for i in range(2):
                    try:
                        helper = quali.helpers.all()[i]
                        col.append(
                            EXPORT_NAMETEL.format(
                                name=helper.get_full_name(), tel=helper.profile.natel
                            )
                            if helper
                            else ""
                        )
                    except IndexError:
                        col.append("")
                col.append(quali.n_participants)
                col.append(quali.n_bikes)
                col.append(quali.n_helmets)
                col.append(str(quali.activity_A) if quali.activity_A else "")
                col.append(str(quali.activity_B) if quali.activity_B else "")
                col.append(str(quali.activity_C) if quali.activity_C else "")
                col.append(
                    EXPORT_NAMETEL.format(
                        name=quali.actor.get_full_name(), tel=quali.actor.profile.natel
                    )
                    if quali.actor
                    else ""
                )
                col.append(quali.comments)
                dataset.append_col(col)
                col = []
        else:
            col += [""] * 13
            dataset.append_col(col)
        return dataset
