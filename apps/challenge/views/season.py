# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016, 2020 Didier Raboud <didier.raboud@liip.ch>
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

import datetime
import operator
import re
from collections import OrderedDict
from functools import reduce

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import warning as warning_message
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.db.models import Case, Count, F, IntegerField, Q, When
from django.http import HttpResponseRedirect
from django.template.defaultfilters import date, time
from django.template.loader import render_to_string
from django.urls import Resolver404, reverse, reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as _p
from django.views.generic import ListView, RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from django_ical.views import ICalFeed
from rolepermissions.checkers import has_role
from rolepermissions.mixins import HasPermissionsMixin
from tablib import Dataset

from apps.common import (
    DV_SEASON_AUTUMN,
    DV_SEASON_CHOICES,
    DV_SEASON_LAST_SPRING_MONTH,
    DV_SEASON_SPRING,
    DV_SEASON_STATE_OPEN,
    DV_SEASON_STATE_RUNNING,
    DV_SEASON_STATES,
    DV_STATES,
)
from apps.common.views import ExportMixin
from apps.user import FORMATION_KEYS, FORMATION_M1, FORMATION_M2
from apps.user.models import USERSTATUS_ACTIVE, USERSTATUS_DELETED, USERSTATUS_RESERVE
from apps.user.views import ActorsList, HelpersList
from defivelo.roles import has_permission, user_cantons
from defivelo.templatetags.dv_filters import dv_season_url
from defivelo.views import MenuView

from .. import (
    AVAILABILITY_FIELDKEY,
    CHOICE_FIELDKEY,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_NOT,
    CHOSEN_KEYS,
    CONFLICT_FIELDKEY,
    SEASON_WORKWISH_FIELDKEY,
    STAFF_FIELDKEY,
    SUPERLEADER_FIELDKEY,
)
from ..forms import (
    SeasonAvailabilityForm,
    SeasonAvailabilityReminderForm,
    SeasonForm,
    SeasonNewHelperAvailabilityForm,
    SeasonStaffChoiceForm,
    SeasonToSpecificStateForm,
)
from ..forms.season import SeasonStaffFilterForm
from ..models import HelperSessionAvailability, Qualification, Season
from ..models.availability import HelperSeasonWorkWish
from ..models.qualification import (
    CATEGORY_CHOICE_A,
    CATEGORY_CHOICE_B,
    CATEGORY_CHOICE_C,
)
from ..utils import (
    GeneralSeason,
    get_users_roles_for_session,
    seasons_in_scope_for_user,
)
from .mixins import CantonSeasonFormMixin

EXPORT_NAMETEL = gettext("{name} - {tel}")


class SeasonMixin(CantonSeasonFormMixin, MenuView):
    required_permission = "challenge_season_crud"
    model = Season
    context_object_name = "season"
    form_class = SeasonForm
    raise_without_cantons = True

    def get_context_data(self, **kwargs):
        context = super(SeasonMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] = "season"
        context["season"] = self.season
        return context

    def get_form_kwargs(self):
        form_kwargs = super(SeasonMixin, self).get_form_kwargs()
        if has_permission(self.request.user, "cantons_all"):
            form_kwargs["cantons"] = DV_STATES
        else:
            # Ne permet que l’édition et la création de moiss pour les cantons gérés
            form_kwargs["cantons"] = self.request.user.managedstates.all().values_list(
                "canton", flat=True
            )
        return form_kwargs

    def get_queryset(self):
        if self.model == Season:
            return self.request.user.profile.get_seasons(
                self.raise_without_cantons
            ).prefetch_related("leader")

        qs = super(SeasonMixin, self).get_queryset()

        if self.model == get_user_model():
            try:
                usercantons = user_cantons(self.request.user)
            except LookupError:
                if self.raise_without_cantons:
                    raise PermissionDenied
                return qs
            # Check that the intersection isn't empty
            cantons = list(set(usercantons).intersection(set(self.season.cantons)))
            if not cantons:
                raise PermissionDenied
        return qs


class SeasonListRedirect(RedirectView):
    is_permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return dv_season_url()


class SeasonListView(SeasonMixin, ListView):
    allow_empty = True
    allow_future = True
    context_object_name = "seasons"
    make_object_list = True
    raise_without_cantons = False

    def dispatch(self, request, *args, **kwargs):
        self.year = int(self.kwargs.pop("year"))
        self.dv_season = self.kwargs.pop("dv_season", None)
        if self.dv_season:
            self.dv_season = int(self.dv_season)
            if self.dv_season not in [s[0] for s in DV_SEASON_CHOICES]:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().filter(year=self.year)
        if self.dv_season == DV_SEASON_SPRING:
            qs = qs.filter(month_start__lte=DV_SEASON_LAST_SPRING_MONTH)
        elif self.dv_season == DV_SEASON_AUTUMN:
            qs = qs.filter(month_start__gt=DV_SEASON_LAST_SPRING_MONTH)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["year"] = self.year
        if self.dv_season:
            context["dv_season"] = self.dv_season
            if self.dv_season == DV_SEASON_SPRING:
                context["dv_season_prev_day"] = datetime.date(
                    self.year - 1, DV_SEASON_LAST_SPRING_MONTH + 1, 1
                )
                context["dv_season_next_day"] = datetime.date(
                    self.year, DV_SEASON_LAST_SPRING_MONTH + 1, 1
                )
            elif self.dv_season == DV_SEASON_AUTUMN:
                context["dv_season_prev_day"] = datetime.date(self.year, 1, 1)
                context["dv_season_next_day"] = datetime.date(self.year + 1, 1, 1)
            else:
                # Will never happen
                raise PermissionDenied
        return context


class SeasonDetailView(SeasonMixin, DetailView):
    allow_season_fetch = True
    raise_without_cantons = False

    def dispatch(self, request, *args, **kwargs):
        """
        Allow view by participants of the season if allowed
        """
        try:
            allowed = False
            if self.season.unprivileged_user_can_see(request.user):
                # Season participants
                allowed = True
            elif has_permission(request.user, self.required_permission):
                # State Managers
                allowed = True

            if allowed:
                return super().dispatch(request, *args, **kwargs)
        except ValueError:
            raise Resolver404
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our submenu_category context
        context["submenu_category"] = "season-detail"
        sessions = self.season.sessions_by_orga
        if not has_permission(self.request.user, "challenge_see_all_orga"):
            sessions = sessions.filter(orga__coordinator=self.request.user)
        context["sessions_by_orga"] = sessions
        return context


class SeasonUpdateView(SeasonMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Mois mis à jour")

    def dispatch(self, request, bypassperm=False, *args, **kwargs):
        if (
            bypassperm
            or
            # Soit j'ai le droit
            has_permission(request.user, self.required_permission)
        ):
            return super(SeasonUpdateView, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


class SeasonHelpersMixin(SeasonMixin):
    """
    Provide helper functions to list helpers for season in various formats
    """

    def potential_helpers_qs(self, qs=None):
        """
        Queryset of potential helpers
        """
        if not qs:
            qs = get_user_model().objects.exclude(profile__status=USERSTATUS_DELETED)
            if self.season:
                seasoncantons = self.season.cantons
                # S'il y au moins un canton en commun
                cantons_filter = [
                    Q(profile__activity_cantons__overlap=seasoncantons)
                ] + [Q(profile__affiliation_canton__in=seasoncantons)]
                qs = qs.filter(reduce(operator.or_, cantons_filter))

            # Pick the one helper from the command line if it makes sense
            resolvermatch = self.request.resolver_match
            try:
                qs = qs.filter(pk=int(resolvermatch.kwargs["helperpk"]))
            except (KeyError, TypeError):
                pass
        return qs.prefetch_related(
            "profile",
            "profile__actor_for",
            "profile__actor_for__translations",
        )

    def potential_helpers(self, qs=None):
        """
        Return the struct of potential helpers, in three blocks
        """
        qs = self.potential_helpers_qs(qs)
        all_helpers = qs.order_by("first_name", "last_name")
        return (
            (
                _("Moniteur·trice·s 2"),
                all_helpers.filter(profile__formation=FORMATION_M2),
            ),
            (
                _("Moniteur·trice·s 1"),
                all_helpers.filter(profile__formation=FORMATION_M1),
            ),
            (
                _("Intervenant·e·s"),
                all_helpers.filter(profile__formation="").exclude(
                    profile__actor_for__isnull=True,
                ),
            ),
        )

    def current_availabilities(self):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        return HelperSessionAvailability.objects.filter(
            session__in=self.object.sessions_with_qualifs
        ).prefetch_related("helper")

    def current_availabilities_present(self):
        return self.current_availabilities().exclude(availability="n")

    @cached_property
    def available_helpers(self):
        # Only take available people
        # Fill in the helpers with the ones we currently have
        helpers_pks = self.current_availabilities_present().values_list(
            "helper_id", flat=True
        )
        return self.potential_helpers(
            qs=get_user_model().objects.filter(pk__in=helpers_pks)
        )

    @cached_property
    def season_helpers(self):
        """
        All the helpers who filled availabilities for this season
        """
        helpers_pks = self.current_availabilities_present().values_list(
            "helper", flat=True
        )
        return get_user_model().objects.filter(pk__in=helpers_pks)


class SeasonAvailabilityMixin(SeasonHelpersMixin):
    view_is_update = False
    view_is_planning = False

    def dispatch(self, request, *args, **kwargs):
        if self._has_default_access(request) or self.custom_access_allowed(request):
            return super().dispatch(request, bypassperm=True, *args, **kwargs)
        raise PermissionDenied

    def _has_default_access(self, request):
        return (
            # Check that the request user is alone in the potential_helpers and we're in season_update
            (
                self.potential_helpers_qs()
                .filter(
                    Q(profile__formation__in=FORMATION_KEYS)
                    | Q(profile__actor_for__isnull=False)
                )
                .filter(pk=request.user.pk)
                .exists()
                and self.season
                and (
                    (
                        self.season.staff_can_update_availability
                        and not self.view_is_planning
                    )
                    or (self.season.staff_can_see_planning and self.view_is_planning)
                )
            )
            or
            # Soit j'ai le droit et c'est le bon moment
            (
                has_permission(request.user, self.required_permission)
                and (not self.view_is_update or self.season.manager_can_crud)
            )
        )

    def custom_access_allowed(self, request):
        # Overridden in aggregated/general-planning views
        return False

    def get_initial(self, all_hsas=None, all_helpers=None):
        initials = OrderedDict()
        if not all_hsas:
            all_hsas = self.current_availabilities()
        if not all_helpers:
            all_helpers = self.potential_helpers()

        if all_hsas:
            all_sessions = self.object.sessions_with_qualifs
            all_wishes = dict(
                self.object.work_wishes.values_list("helper_id", "amount")
            )
            potential_conflicts = (
                HelperSessionAvailability.objects
                # Ne boucle pas
                .exclude(session__id__in=all_sessions)
                # Seulement des sessions concernées
                .filter(session__day__in=all_sessions.values_list("day", flat=True))
                # Seulement dans les états qui nous intéressent
                .filter(chosen_as__in=CHOSEN_KEYS)
                .prefetch_related("session", "session__orga")
            )
            for helper_category, helpers in all_helpers:
                helpers_conflicts = list(potential_conflicts.filter(helper__in=helpers))

                for helper in helpers:
                    helper_availability = {
                        a.session_id: a for a in all_hsas if a.helper == helper
                    }
                    # Fill in the wishes
                    initials[SEASON_WORKWISH_FIELDKEY.format(hpk=helper.pk)] = (
                        all_wishes[helper.pk] if helper.pk in all_wishes else 0
                    )

                    for session in all_sessions:
                        fieldkey = AVAILABILITY_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk
                        )
                        staffkey = STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)
                        choicekey = CHOICE_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk
                        )
                        conflictkey = CONFLICT_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk
                        )
                        superleaderkey = SUPERLEADER_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk
                        )
                        try:
                            hsa = helper_availability[session.id]
                            initials[fieldkey] = hsa.availability
                            # Si un choix est fait _dans_ une session (qualif)
                            initials[staffkey] = session.user_assignment(helper)
                            initials[choicekey] = True
                            # Le choix n’est fait qu'au niveau de la session
                            if not initials[staffkey]:
                                initials[staffkey] = hsa.chosen_as
                                initials[choicekey] = False
                        except Exception:
                            initials[fieldkey] = ""
                            initials[staffkey] = ""
                            initials[choicekey] = ""
                        # List super-leaders (Moniteurs +)
                        if session.superleader == helper:
                            initials[superleaderkey] = True

                        # Trouve les disponibilités en conflit
                        initials[conflictkey] = [
                            hc.session
                            for hc in helpers_conflicts
                            if hc.helper_id == helper.pk
                            and hc.session.day == session.day
                        ]
            return initials

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resolvermatch = self.request.resolver_match
        try:
            context["helperpk"] = resolvermatch.kwargs["helperpk"]
        except (KeyError, TypeError):
            pass

        context["user_can_see_season"] = self.season.unprivileged_user_can_see(
            self.request.user
        )
        # Add our submenu_category context
        context["submenu_category"] = "season-availability"
        context["sessions"] = self.object.sessions_with_qualifs.annotate(
            n_qualifs=Count("qualifications", distinct=True),
            n_leaders=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_LEADER,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
            n_helpers=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_HELPER,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
            n_actors=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_ACTOR,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
        )
        return context


class SeasonToStateMixin(SeasonHelpersMixin, SeasonUpdateView):
    form_class = SeasonToSpecificStateForm
    season_to_state = None
    template_name = "challenge/season_form_tostate.html"

    def get_form_kwargs(self):
        """
        Hand over tostate to the Form class
        """
        form_kwargs = super().get_form_kwargs()
        form_kwargs["tostate"] = self.season_to_state
        return form_kwargs

    def get_context_data(self, **kwargs):
        """
        Set tostate to the verbose desired state
        """
        context = super().get_context_data(**kwargs)
        context["tostate"] = next(
            (v for (k, v) in DV_SEASON_STATES if k == self.season_to_state)
        )
        context["recipients"] = self.season_helpers
        return context

    def get_initial(self):
        """
        Set the inital form value to the state we target
        """
        return {"state": self.season_to_state}

    def dispatch(self, request, bypassperm=False, *args, **kwargs):
        """
        Push away if we're already in the given state
        """
        if self.season and self.season.state == self.season_to_state:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SeasonToRunningView(SeasonToStateMixin):
    season_to_state = DV_SEASON_STATE_RUNNING

    def get_email(self, profile=None):
        """
        Get a simple struct with the email we're sending at this step
        """
        if profile:
            helperpk = profile.pk
        else:
            # Fake a profile that can be used in template
            profile = {"get_full_name": _("{Prénom} {Nom}")}
            helperpk = 0

        planning_link = self.request.build_absolute_uri(
            reverse(
                "season-planning",
                kwargs={"pk": self.season.pk, "helperpk": helperpk},
            )
        )

        return {
            "subject": settings.EMAIL_SUBJECT_PREFIX
            + gettext("Planning {season}").format(season=self.season.desc()),
            "body": {
                "pre": render_to_string(
                    "challenge/season_email_to_state_running_pre.txt",
                    {
                        "profile": profile,
                        "season": self.season,
                        "planning_link": planning_link,
                        "current_site": Site.objects.get_current(),
                    },
                ),
                "post": render_to_string(
                    "challenge/season_email_to_state_running_post.txt",
                    {
                        "profile": profile,
                        "season": self.season,
                        "planning_link": planning_link,
                        "current_site": Site.objects.get_current(),
                    },
                ),
            },
        }

    def dispatch(self, request, bypassperm=False, *args, **kwargs):
        """
        Push away if we're not allowed to go to that state now
        """
        if self.season and self.season.can_set_state_running:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["some_recipients_cant_login"] = any(
            not user.profile.can_login for user in context["recipients"]
        )
        context["email"] = self.get_email()
        return context

    def form_valid(self, form):
        """
        Run our specific action here
        """
        # Save first
        form_result = super().form_valid(form)
        if form.cleaned_data["sendemail"]:
            for helper in self.season_helpers:
                email = self.get_email(helper)
                body = "\n".join(
                    [
                        email["body"]["pre"],
                        form.cleaned_data["customtext"],
                        email["body"]["post"],
                    ]
                )
                helper.profile.send_mail(email["subject"], body)
        return form_result


class SeasonToOpenView(SeasonToStateMixin):
    season_to_state = DV_SEASON_STATE_OPEN

    def get_email(self, profile=None):
        """
        Get a simple struct with the email we're sending at this step
        """
        if profile:
            helperpk = profile.pk
        else:
            # Fake a profile that can be used in template
            profile = {"get_full_name": _("{Prénom} {Nom}")}
            helperpk = 0

        planning_link = self.request.build_absolute_uri(
            reverse(
                "season-availabilities-update",
                kwargs={"pk": self.season.pk, "helperpk": helperpk},
            )
        )

        return {
            "subject": settings.EMAIL_SUBJECT_PREFIX
            + gettext("Planning {season}").format(season=self.season.desc()),
            "body": {
                "pre": render_to_string(
                    "challenge/season_email_to_state_open_pre.txt",
                    {
                        "profile": profile,
                        "season": self.season,
                        "planning_link": planning_link,
                        "current_site": Site.objects.get_current(),
                    },
                ),
                "post": render_to_string(
                    "challenge/season_email_to_state_open_post.txt",
                    {
                        "profile": profile,
                        "season": self.season,
                        "planning_link": planning_link,
                        "current_site": Site.objects.get_current(),
                    },
                ),
            },
        }

    def dispatch(self, request, bypassperm=False, *args, **kwargs):
        """
        Push away if we're not allowed to go to that state now
        """
        if self.season and self.season.can_set_state_open:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get_email_recipients(self):
        """
        List of potential helpers/actors that we want to notify.
        This might include users that can't login.
        """
        return (
            self.potential_helpers_qs()
            .filter(profile__status__in=(USERSTATUS_ACTIVE, USERSTATUS_RESERVE))
            .exclude(Q(profile__formation="") & Q(profile__actor_for__isnull=True))
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipients = list(
            self.get_email_recipients().order_by("first_name", "last_name", "id")
        )
        context["recipients"] = recipients
        context["some_recipients_cant_login"] = any(
            not user.profile.can_login for user in recipients
        )
        context["email"] = self.get_email()
        return context

    def form_valid(self, form):
        """
        Run our specific action here
        """
        # Save first
        form_result = super().form_valid(form)
        if form.cleaned_data["sendemail"]:
            # Then send emails
            for helper in self.get_email_recipients():
                email = self.get_email(helper)
                body = "\n".join(
                    [
                        email["body"]["pre"],
                        form.cleaned_data["customtext"],
                        email["body"]["post"],
                    ]
                )
                helper.profile.send_mail(email["subject"], body)
        return form_result


class SeasonAvailabilityReminderView(SeasonHelpersMixin, SeasonUpdateView):
    template_name = "challenge/season_availability_reminder.html"
    form_class = SeasonAvailabilityReminderForm

    def get_email(self, profile=None):
        if profile:
            helperpk = profile.pk
        else:
            profile = {"get_full_name": _("{Prénom} {Nom}")}
            helperpk = 0

        planning_link = self.request.build_absolute_uri(
            reverse(
                "season-availabilities-update",
                kwargs={"pk": self.season.pk, "helperpk": helperpk},
            )
        )

        pre = render_to_string(
            "challenge/season_email_availability_reminder.txt",
            {
                "profile": profile,
                "season": self.season,
                "planning_link": planning_link,
                "current_site": Site.objects.get_current(),
            },
        )

        return {
            "subject": settings.EMAIL_SUBJECT_PREFIX
            + gettext("Planning {season}").format(season=self.season.desc()),
            "body": {"pre": pre},
        }

    def get_email_recipients(self):
        base_qs = (
            self.potential_helpers_qs()
            .filter(profile__status__in=(USERSTATUS_ACTIVE, USERSTATUS_RESERVE))
            .exclude(Q(profile__formation="") & Q(profile__actor_for__isnull=True))
            .distinct()
        )
        sessions_qs = self.season.sessions_with_qualifs
        if not sessions_qs.exists():
            return base_qs.none()

        total_sessions = sessions_qs.count()

        # Helpers who have availabilities for all sessions (fully filled)
        fully_filled_helper_ids = (
            HelperSessionAvailability.objects.filter(session__in=sessions_qs)
            .values("helper_id")
            .annotate(n=Count("session", distinct=True))
            .filter(n=total_sessions)
            .values_list("helper_id", flat=True)
        )
        # Send to helpers not fully filled (partial or none)
        return base_qs.exclude(id__in=fully_filled_helper_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipients = list(
            self.get_email_recipients().order_by("first_name", "last_name", "id")
        )
        context["recipients"] = recipients
        context["some_recipients_cant_login"] = any(
            not user.profile.can_login for user in recipients
        )
        context["email"] = self.get_email()
        return context

    def form_valid(self, form):
        form_result = super().form_valid(form)
        if not form.cleaned_data.get("sendemail"):
            return form_result
        now = timezone.now()
        for helper in self.get_email_recipients():
            email = self.get_email(helper)
            body = email["body"]["pre"]
            helper.profile.send_mail(email["subject"], body)

        self.object.availability_reminder_sent_at = now
        self.object.save()
        return form_result


class SeasonExportView(
    ExportMixin, SeasonAvailabilityMixin, HasPermissionsMixin, DetailView
):
    @property
    def export_filename(self):
        return _p("Singular month", "Mois") + "-" + "-".join(self.season.cantons)

    def undetected_translations(self):
        return [
            # Translators: Intervenant
            _("Int."),
            # Translators: Moniteur·trice + / Photographe
            _("M+"),
        ]

    def get_dataset(self):
        dataset = Dataset()
        # Prépare le fichier
        dataset.append_col(
            [
                gettext("Date"),
                gettext("Canton"),
                gettext("Établissement"),
                gettext("Emplacement"),
                gettext("Heures"),
                gettext("Nombre de qualifs"),
                # Logistique
                gettext("Moniteur·trice + / Photographe"),
                gettext("Mauvais temps"),
                gettext("Logistique vélos"),
                gettext("N° de contact vélos"),
                gettext("Pommes"),
                gettext("Total vélos"),
                gettext("Total casques"),
                gettext("Remarques"),
                # Qualif
                gettext("Classe"),
                gettext("Enseignant·e"),
                gettext("Moniteur·trice 2"),
                gettext("Moniteur·trice 1"),
                gettext("Moniteur·trice 1"),
                gettext("Nombre d’élèves"),
                gettext("Nombre de vélos"),
                gettext("Nombre de casques"),
                str(CATEGORY_CHOICE_A),
                str(CATEGORY_CHOICE_B),
                str(CATEGORY_CHOICE_C),
                gettext("Intervenant·e"),
                gettext("Remarques"),
            ]
        )
        for session in self.season.sessions:
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
                            name=quali.class_teacher_fullname,
                            tel=quali.class_teacher_natel,
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
                                    name=helper.get_full_name(),
                                    tel=helper.profile.natel,
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
                            name=quali.actor.get_full_name(),
                            tel=quali.actor.profile.natel,
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


class GeneralPlanningSupportMixin(object):
    """
    Shared logic to support "general" planning (aggregated across months) for
    export views and feeds.
    """

    def _is_general_planning(self):
        return "year" in self.kwargs and "dv_season" in self.kwargs

    def _seasons_in_scope(self):
        try:
            year = int(self.kwargs.get("year"))
            dv_season = int(self.kwargs.get("dv_season"))
        except (TypeError, ValueError):
            return None, None, []
        qs = seasons_in_scope_for_user(self.request.user, year, dv_season)
        return year, dv_season, list(qs)

    def _helperpk_in_kwargs(self):
        helperpk_raw = self.kwargs.get("helperpk")
        try:
            helperpk = int(helperpk_raw) if helperpk_raw is not None else None
        except (TypeError, ValueError):
            helperpk = None
        return helperpk

    def _general_object(self):
        year, dv_season, seasons = self._seasons_in_scope()
        return GeneralSeason(
            year=year,
            dv_season=dv_season,
            seasons=seasons,
            helper_id=self._helperpk_in_kwargs(),
        )

    def _general_access_allowed(self, request):
        # Managers always
        permission_name = getattr(self, "required_permission", "challenge_season_crud")
        if has_permission(request.user, permission_name):
            return True
        # Helpers if any season is running
        _, _, seasons = self._seasons_in_scope()
        user_is_helper = request.user.profile.is_paid_staff and (
            request.user.profile.actor or request.user.profile.formation
        )
        any_running = any(s.staff_can_see_planning for s in seasons)
        if user_is_helper and any_running:
            return True
        return False

    def get_object(self, queryset=None):
        if self._is_general_planning():
            return self._general_object()
        return super().get_object(queryset)

    def dispatch(self, request, *args, **kwargs):
        if self._is_general_planning():
            if self._general_access_allowed(request):
                return super().dispatch(request, *args, **kwargs)
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def custom_access_allowed(self, request):
        if self._is_general_planning():
            return self._general_access_allowed(request)
        return False


class SeasonPersonalPlanningExportView(
    GeneralPlanningSupportMixin, ExportMixin, SeasonAvailabilityMixin, DetailView
):
    allow_season_fetch = True
    raise_without_cantons = False
    view_is_planning = True

    @property
    def export_filename(self):
        # Support aggregated season (general planning)
        if hasattr(self.object, "dv_season"):
            label = _(slugify("Planning général"))
            return label + "-" + str(self.object.year)
        return _(slugify("Planning mois")) + "-" + "-".join(self.object.cantons)

    def get(self, request, *args, **kwargs):
        # Bypass SeasonAvailabilityMixin.get_context_data to avoid self.season usage in aggregated mode
        self.object = self.get_object()
        return self.render_to_response({})

    def get_dataset(self):
        dataset = Dataset()
        firstcol = [
            gettext("Date"),
            gettext("Canton"),
            gettext("Établissement"),
            gettext("Emplacement"),
            gettext("Heures"),
            gettext("Nombre de qualifs"),
        ]
        # Trouve toutes les personnes qui sont présentes dans ce mois / période
        qs = get_user_model().objects
        user_filters = [
            # Ceux qui ont répondu (quoi que ce soit)
            Q(availabilities__session__in=self.object.sessions_with_qualifs),
            # Moniteurs +
            Q(sess_monplus__in=self.object.sessions_with_qualifs),
            # Moniteurs 2
            Q(qualifs_mon2__session__in=self.object.sessions_with_qualifs),
            # Moniteurs 1
            Q(qualifs_mon1__session__in=self.object.sessions_with_qualifs),
            # Intervenants
            Q(qualifs_actor__session__in=self.object.sessions_with_qualifs),
        ]
        # Get users that match any filter in `user_filters`.
        # We used to do it in a single DB query with OR clauses,
        # but the production DB would execute this query in multiple minutes!
        user_ids = set()
        for user_filter in user_filters:
            user_ids.update(qs.filter(user_filter).values_list("id", flat=True))
        qs = (
            qs.filter(id__in=user_ids)
            .order_by("first_name", "last_name")
            .select_related("profile")
        )
        resolvermatch = self.request.resolver_match
        try:
            qs = qs.filter(pk=int(resolvermatch.kwargs["helperpk"]))
        except (KeyError, TypeError):
            pass

        firstcol += [user.get_full_name() for user in qs]
        dataset.append_col(firstcol)
        # Ajoute le canton d’affiliation comme deuxième colonne
        user_cantons_col = [""] * 6 + [user.profile.affiliation_canton for user in qs]
        dataset.append_col(user_cantons_col)
        # Limit sessions to those with a staff choice/assignment for the requested helper in aggregated mode
        sessions_qs = self.object.sessions_with_qualifs
        if hasattr(self.object, "dv_season"):
            resolvermatch = self.request.resolver_match
            try:
                helperpk = int(resolvermatch.kwargs["helperpk"])
            except (KeyError, TypeError):
                helperpk = None
            if helperpk:
                # Include sessions where the helper is assigned in any qualification
                chosen_ids = set(
                    sessions_qs.filter(
                        Q(qualifications__leader_id=helperpk)
                        | Q(qualifications__helpers__id=helperpk)
                        | Q(qualifications__actor_id=helperpk)
                    ).values_list("id", flat=True)
                )
                if chosen_ids:
                    sessions_qs = sessions_qs.filter(pk__in=chosen_ids)
                else:
                    sessions_qs = sessions_qs.none()

        for session in sessions_qs:
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
            ]
            users_roles = list(get_users_roles_for_session(qs, session).values())
            col += users_roles
            dataset.append_col(col)
        return dataset


class SeasonPlanningExportView(SeasonPersonalPlanningExportView, HasPermissionsMixin):
    view_is_planning = False


class SeasonAvailabilityView(SeasonAvailabilityMixin, DetailView):
    template_name = "challenge/season_availability.html"

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityView, self).get_context_data(**kwargs)
        # Add the form for picking a new helper
        context["form"] = SeasonNewHelperAvailabilityForm(cantons=self.season.cantons)
        hsas = self.current_availabilities()
        if hsas:
            # Fill in the helpers with the ones we currently have
            helpers_pks = self.current_availabilities().values_list(
                "helper_id", flat=True
            )
            potential_helpers = self.potential_helpers(
                qs=get_user_model().objects.filter(pk__in=helpers_pks)
            )

            context["potential_helpers"] = potential_helpers
            context["availabilities"] = self.get_initial(
                all_hsas=hsas, all_helpers=potential_helpers
            )
        return context

    def post(self, request, *args, **kwargs):
        seasonpk = kwargs.get("pk", None)
        form = SeasonNewHelperAvailabilityForm(request.POST)
        if form.is_valid():
            helper = form.cleaned_data["helper"]
            return HttpResponseRedirect(
                reverse_lazy(
                    "season-availabilities-update",
                    kwargs={"pk": seasonpk, "helperpk": helper.pk},
                )
            )
        return HttpResponseRedirect(
            reverse_lazy("season-availabilities", kwargs={"pk": seasonpk})
        )


class SeasonPlanningView(SeasonAvailabilityMixin, DetailView):
    template_name = "challenge/season_planning.html"
    allow_season_fetch = True
    raise_without_cantons = False
    view_is_planning = True

    def dispatch(self, request, *args, **kwargs):
        """
        Early request processing dispatch
        """
        try:
            """
            DEFIVELO-221 Circumvent a weird bug that made it so that emails were sent with helperpk == 0
            If helperpk == 0, redirect to self
            """
            if (
                self.request.user
                and int(self.request.resolver_match.kwargs["helperpk"]) == 0
            ):
                return HttpResponseRedirect(
                    reverse_lazy(
                        "season-planning",
                        kwargs={
                            "pk": self.season.pk,
                            "helperpk": self.request.user.pk,
                        },
                    )
                )

            """
            DEFIVELO-221 If we're in the wrong state, redirect to the other URL; move from planning to availability
            """
            if (
                self.request.user.profile.is_paid_staff
                and (
                    self.request.user.profile.actor
                    or self.request.user.profile.formation
                )
                and not self.season.staff_can_see_planning
                and self.season.staff_can_update_availability
            ):
                warning_message(
                    request,
                    _(
                        "Le planning n'est pas encore disponible; mets plutôt à jour tes disponibilités."
                    ),
                )
                return HttpResponseRedirect(
                    reverse_lazy(
                        "season-availabilities-update",
                        kwargs={
                            "pk": self.season.pk,
                            "helperpk": self.request.user.pk,
                        },
                    )
                )
        except KeyError:
            pass
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        potential_helpers = self.potential_helpers()
        context["submenu_category"] = "season-planning"
        context["potential_helpers"] = potential_helpers
        context["availabilities"] = (
            self.get_initial(all_helpers=potential_helpers) or {}
        )
        return context


class SeasonGeneralPlanningView(SeasonAvailabilityMixin, DetailView):
    template_name = "challenge/season_planning.html"
    allow_season_fetch = True
    raise_without_cantons = False
    view_is_planning = True

    def _seasons_in_scope(self):
        year = int(self.kwargs.get("year"))
        dv_season = int(self.kwargs.get("dv_season"))
        qs = seasons_in_scope_for_user(self.request.user, year, dv_season)
        return year, dv_season, list(qs)

    def get_object(self, queryset=None):
        year, dv_season, seasons = self._seasons_in_scope()
        helperpk_raw = self.kwargs.get("helperpk")
        try:
            helperpk = int(helperpk_raw) if helperpk_raw is not None else None
        except (TypeError, ValueError):
            helperpk = None
        return GeneralSeason(
            year=year, dv_season=dv_season, seasons=seasons, helper_id=helperpk
        )

    def dispatch(self, request, *args, **kwargs):
        helperpk_raw = self.kwargs.get("helperpk")
        if self.request.user and helperpk_raw is not None:
            try:
                if int(helperpk_raw) == 0:
                    year = int(self.kwargs.get("year"))
                    dv_season = int(self.kwargs.get("dv_season"))
                    return HttpResponseRedirect(
                        reverse_lazy(
                            "season-general-planning",
                            kwargs={
                                "year": year,
                                "dv_season": dv_season,
                                "helperpk": self.request.user.pk,
                            },
                        )
                    )
            except (TypeError, ValueError):
                pass

        # Authorization logic similar to SeasonPlanningView, adapted for aggregated seasons
        if has_permission(request.user, self.required_permission):
            return super().dispatch(request, *args, **kwargs)

        year, dv_season, seasons = self._seasons_in_scope()
        user_is_helper = request.user.profile.is_paid_staff and (
            request.user.profile.actor or request.user.profile.formation
        )
        any_running = any(s.staff_can_see_planning for s in seasons)
        any_open = any(s.staff_can_update_availability for s in seasons)
        if user_is_helper and any_running:
            return super().dispatch(request, *args, **kwargs)
        if user_is_helper and any_open:
            # Mirror the redirect used in SeasonPlanningView when planning isn't available
            target = next((s for s in seasons if s.staff_can_update_availability), None)
            if target:
                warning_message(
                    request,
                    _(
                        "Le planning n'est pas encore disponible. En attendant, vous pouvez mettre à jour vos disponibilités."
                    ),
                )
                return HttpResponseRedirect(
                    reverse_lazy(
                        "season-availabilities-update",
                        kwargs={"pk": target.pk, "helperpk": request.user.pk},
                    )
                )

        raise PermissionDenied

    def custom_access_allowed(self, request):
        # Allow aggregated general planning when appropriate; default rules handled in dispatch for redirects
        if has_permission(request.user, self.required_permission):
            return True
        year, dv_season, seasons = self._seasons_in_scope()
        user_is_helper = request.user.profile.is_paid_staff and (
            request.user.profile.actor or request.user.profile.formation
        )
        any_running = any(s.staff_can_see_planning for s in seasons)
        if user_is_helper and any_running:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = DetailView.get_context_data(self, **kwargs)
        context["season"] = self.object

        helperpk_raw = self.kwargs.get("helperpk")
        try:
            helperpk = (
                int(helperpk_raw)
                if helperpk_raw is not None
                else int(self.request.user.pk)
            )
        except (TypeError, ValueError):
            helperpk = int(self.request.user.pk)

        potential_helpers = self.potential_helpers(
            qs=get_user_model().objects.filter(pk=helperpk)
        )
        context["submenu_category"] = "season-planning"
        context["helperpk"] = helperpk
        context["potential_helpers"] = potential_helpers
        context["availabilities"] = (
            self.get_initial(all_helpers=potential_helpers) or {}
        )
        if not context["availabilities"]:
            context["availabilities"] = OrderedDict()

        chosen_session_ids = set()
        choice_prefix = CHOICE_FIELDKEY.format(hpk=helperpk, spk="").replace("-s", "")
        for key, val in context["availabilities"].items():
            m = re.search(r"^" + re.escape(choice_prefix) + r"-s(\d+)$", key)
            if m and val:
                try:
                    chosen_session_ids.add(int(m.group(1)))
                except ValueError:
                    pass
        base_sessions = self.object.sessions_with_qualifs
        filtered_sessions = base_sessions.filter(pk__in=chosen_session_ids).annotate(
            n_qualifs=Count("qualifications", distinct=True),
            n_leaders=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_LEADER,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
            n_helpers=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_HELPER,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
            n_actors=Count(
                Case(
                    When(
                        availability_statuses__chosen_as=CHOSEN_AS_ACTOR,
                        then=F("availability_statuses__id"),
                    ),
                    output_field=IntegerField(),
                ),
                distinct=True,
            ),
        )
        context["sessions"] = filtered_sessions

        allowed_ids = set(filtered_sessions.values_list("pk", flat=True))
        pruned = OrderedDict()
        for key, value in context["availabilities"].items():
            m = re.search(r"-s(\d+)", key)
            if m:
                try:
                    spk = int(m.group(1))
                except ValueError:
                    spk = None
                if spk in allowed_ids:
                    # For availability entries, keep only if corresponding choice is True
                    if AVAILABILITY_FIELDKEY.format(hpk=helperpk, spk="") in key:
                        choice_key = CHOICE_FIELDKEY.format(hpk=helperpk, spk=spk)
                        if context["availabilities"].get(choice_key):
                            pruned[key] = value
                    else:
                        pruned[key] = value
            else:
                pruned[key] = value
        context["availabilities"] = pruned

        _, _, seasons = self._seasons_in_scope()
        context["user_can_see_season"] = any(
            s.unprivileged_user_can_see(self.request.user) for s in seasons
        )
        return context


class SeasonAvailabilityUpdateView(SeasonAvailabilityMixin, SeasonUpdateView):
    template_name = "challenge/season_availability_update.html"
    success_message = _("Disponibilités mises à jour")
    form_class = SeasonAvailabilityForm
    allow_season_fetch = True
    raise_without_cantons = False
    view_is_update = True

    def dispatch(self, request, *args, **kwargs):
        """
        Early request processing dispatch
        """
        try:
            """
            DEFIVELO-221 Circumvent a weird bug that made it so that emails were sent with helperpk == 0
            If helperpk == 0, redirect to self
            """
            if (
                self.request.user
                and int(self.request.resolver_match.kwargs["helperpk"]) == 0
            ):
                return HttpResponseRedirect(
                    reverse_lazy(
                        "season-availabilities-update",
                        kwargs={
                            "pk": self.season.pk,
                            "helperpk": self.request.user.pk,
                        },
                    )
                )
            """
            DEFIVELO-221 If we're in the wrong state, redirect to the other URL; move from planning to availability
            """
            if (
                # Poweruser & Related state manager, can still access
                not self.request.user.managedstates.filter(
                    canton__in=self.season.cantons
                ).exists()
                and not has_role(self.request.user, "power_user")
                and (
                    self.request.user.profile.actor
                    or self.request.user.profile.formation
                )
                and not self.season.staff_can_update_availability
                and self.season.staff_can_see_planning
            ):
                warning_message(
                    request,
                    _(
                        "Il n'est pas possible de mettre à jour tes disponibilités; voici le planning."
                    ),
                )
                return HttpResponseRedirect(
                    reverse_lazy(
                        "season-planning",
                        kwargs={
                            "pk": self.season.pk,
                            "helperpk": self.request.user.pk,
                        },
                    )
                )
        except KeyError:
            pass
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super(SeasonAvailabilityUpdateView, self).get_form_kwargs()
        form_kwargs["potential_helpers"] = self.potential_helpers()
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(SeasonAvailabilityUpdateView, self).get_context_data(**kwargs)
        context["potential_helpers"] = self.potential_helpers()
        return context

    def get_success_url(self):
        try:
            usercantons = user_cantons(self.request.user)
        except LookupError:
            usercantons = None
        if has_permission(self.request.user, "challenge_season_crud") and list(
            set(usercantons).intersection(set(self.season.cantons))
        ):
            return reverse_lazy("season-availabilities", kwargs={"pk": self.season.pk})
        else:
            return reverse_lazy(
                "season-availabilities-update",
                kwargs={
                    "pk": self.season.pk,
                    "helperpk": self.request.user.pk,
                },
            )

    def form_valid(self, form):
        # Create or update the Availability objects
        for session in self.object.sessions_with_qualifs:
            for helper_category, helpers in self.potential_helpers():
                for helper in helpers:
                    # Fill in the wishes
                    workwishkey = SEASON_WORKWISH_FIELDKEY.format(hpk=helper.pk)
                    if workwishkey in form.cleaned_data:
                        amount = form.cleaned_data[workwishkey]
                        try:
                            (hww, created) = HelperSeasonWorkWish.objects.get_or_create(
                                season=self.season,
                                helper=helper,
                                defaults={"amount": amount},
                            )
                        except HelperSeasonWorkWish.MultipleObjectsReturned:
                            # Too many of these, for some reason. Take the latest.
                            hww = HelperSeasonWorkWish.objects.filter(
                                season=self.season, helper=helper
                            ).order_by("-id")[0]
                            created = False
                        if not created:
                            hww.amount = amount
                            hww.save()

                    # Fill in the availabilities
                    fieldkey = AVAILABILITY_FIELDKEY.format(
                        hpk=helper.pk, spk=session.pk
                    )
                    if fieldkey in form.cleaned_data:
                        availability = form.cleaned_data[fieldkey]
                        if availability:
                            (
                                hsa,
                                created,
                            ) = HelperSessionAvailability.objects.get_or_create(
                                session=session,
                                helper=helper,
                                defaults={"availability": availability},
                            )
                            if not created:
                                hsa.availability = availability
                                hsa.save()
        return super(SeasonAvailabilityUpdateView, self).form_valid(form)


class SeasonStaffChoiceUpdateView(
    SeasonAvailabilityMixin, SeasonUpdateView, HasPermissionsMixin
):
    template_name = "challenge/season_staff_update.html"
    success_message = _("Choix du personnel mises à jour")
    form_class = SeasonStaffChoiceForm
    form_filter_class = SeasonStaffFilterForm
    view_is_update = True

    def get_initial(self):
        # Shortcut through giving only the available_helpers
        return super(SeasonStaffChoiceUpdateView, self).get_initial(
            all_hsas=None, all_helpers=self.available_helpers
        )

    def get_form_kwargs(self):
        form_kwargs = super(SeasonStaffChoiceUpdateView, self).get_form_kwargs()
        form_kwargs["available_helpers"] = self.available_helpers
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(SeasonStaffChoiceUpdateView, self).get_context_data(**kwargs)
        context["available_helpers"] = self.available_helpers
        context["season_staff_filter_form"] = SeasonStaffFilterForm(
            organisations=self._extract_orgas(context["sessions"])
        )
        context["availabilities"] = self.get_initial()
        return context

    def form_valid(self, form):
        # Update all staff choices
        for session in self.object.sessions_with_qualifs:
            session_helpers = {}  # Those picked for the season
            session_non_helpers = {}  # Those not picked for the season
            for helper_category, helpers in self.available_helpers:
                for helper in helpers:
                    fieldkey = STAFF_FIELDKEY.format(hpk=helper.pk, spk=session.pk)

                    try:
                        chosen_as = int(form.cleaned_data[fieldkey])

                        HelperSessionAvailability.objects.filter(
                            session=session, helper=helper
                        ).update(chosen_as=chosen_as)
                    except ValueError:
                        chosen_as = None

                    if chosen_as != CHOSEN_AS_NOT:
                        session_helpers[helper.pk] = helper
                    else:
                        session_non_helpers[helper.pk] = helper

            # Do a session-wide check across all helpers picked for that
            # session
            for quali in session.qualifications.all():
                for non_helper in session_non_helpers.values():
                    # Drop those not in the session anymore
                    if non_helper == quali.leader:
                        quali.leader = None
                    if non_helper in quali.helpers.all():
                        quali.helpers.remove(helper)
                    if non_helper == quali.actor:
                        quali.actor = None
                quali.save()
        return HttpResponseRedirect(
            reverse_lazy("season-availabilities", kwargs={"pk": self.object.pk})
        )

    def _extract_orgas(self, sessions):
        seen_ids = set()
        orgas = []
        for session in sessions:
            if session.orga and session.orga_id not in seen_ids:
                seen_ids.add(session.orga_id)
                orgas.append(session.orga)
        return orgas


class SeasonCreateView(
    SeasonMixin, HasPermissionsMixin, SuccessMessageMixin, CreateView
):
    success_message = _("Mois créé")


class SeasonHelperListView(HelpersList, HasPermissionsMixin, SeasonMixin):
    model = get_user_model()
    page_title = _("Moniteur·trice·s du mois")

    def get_context_data(self, **kwargs):
        context = super(SeasonHelperListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context["submenu_category"] = "season-helperlist"
        return context

    def get_queryset(self):
        return (
            super(SeasonHelperListView, self)
            .get_queryset()
            .filter(
                Q(qualifs_mon2__session__in=self.season.sessions_with_qualifs)
                | Q(qualifs_mon1__session__in=self.season.sessions_with_qualifs),
            )
            .distinct()
        )


class SeasonActorListView(ActorsList, HasPermissionsMixin, SeasonMixin):
    model = get_user_model()
    page_title = _("Intervenant·e·s du mois")

    def get_context_data(self, **kwargs):
        context = super(SeasonActorListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context["submenu_category"] = "season-actorslist"
        return context

    def get_queryset(self):
        return (
            super(SeasonActorListView, self)
            .get_queryset()
            .filter(qualifs_actor__session__in=self.season.sessions_with_qualifs)
            .distinct()
        )


class SeasonErrorsListView(HasPermissionsMixin, SeasonMixin, ListView):
    required_permission = "challenge_season_crud"
    model = Qualification
    page_title = _("Erreurs dans les qualifs du mois")
    template_name = "challenge/season_errors.html"
    context_object_name = "qualifs"

    def get_context_data(self, **kwargs):
        context = super(SeasonErrorsListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context["submenu_category"] = "season-errorslist"
        return context

    def get_queryset(self):
        wrong_qualifs = []
        for session in self.season.sessions_with_qualifs.all():
            for quali in session.qualifications.all():
                if quali.has_availability_incoherences:
                    wrong_qualifs.append(quali.pk)
        return (
            super(SeasonErrorsListView, self)
            .get_queryset()
            .filter(pk__in=wrong_qualifs)
            .distinct()
        )


class SeasonPersonalPlanningExportFeed(GeneralPlanningSupportMixin, ICalFeed):
    timezone = datetime.timezone.utc
    file_name = "sessions.ics"

    def __call__(self, request, *args, **kwargs):
        self.request = request
        self.kwargs = kwargs
        resolvermatch = self.request.resolver_match
        self.user = get_user_model().objects.get(
            pk=int(resolvermatch.kwargs["helperpk"])
        )

        # Support "general" planning scope via the shared mixin
        if self._is_general_planning():
            if not self._general_access_allowed(request):
                raise PermissionDenied
            self.object = self.season = self._general_object()
        else:
            self.object = self.season = Season.objects.get(pk=kwargs.get("pk"))
        return super().__call__(request)

    def items(self):
        return self.object.sessions_with_qualifs.filter(
            Q(superleader=self.user)
            | Q(qualifications__actor=self.user)
            | Q(qualifications__helpers=self.user)
            | Q(qualifications__leader=self.user)
        )

    def item_guid(self, session):
        return "{}-{}".format(session.id, "session")

    def item_title(self, session):
        roles_by_user = get_users_roles_for_session([self.user], session)
        role_label = roles_by_user[self.user]
        return " ".join([role_label, session.orga.address_canton, session.orga.name])

    def item_description(self, session):
        session_place = session.place
        if not session_place:
            session_place = (
                session.address_city
                if session.address_city
                else session.orga.address_city
            )
        return " ".join(
            [
                session_place,
                "%s - %s" % (time(session.begin), time(session.end)),
            ]
        )

    def item_start_datetime(self, session):
        return session.start_datetime.astimezone(datetime.timezone.utc)

    def item_end_datetime(self, session):
        return session.end_datetime.astimezone(datetime.timezone.utc)

    def item_link(self, session):
        # Link back to the appropriate planning page depending on mode
        if hasattr(self.object, "dv_season"):
            return reverse(
                "season-general-planning",
                kwargs={
                    "year": self.object.year,
                    "dv_season": self.object.dv_season,
                    "helperpk": self.user.id,
                },
            )
        return reverse(
            "season-planning", kwargs={"pk": self.season.pk, "helperpk": self.user.id}
        )
