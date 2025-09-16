import datetime
from datetime import time
from typing import Mapping

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils.translation import gettext
from django.utils.translation import gettext as _

from apps.common import DV_SEASON_AUTUMN, DV_SEASON_LAST_SPRING_MONTH, DV_SEASON_SPRING
from apps.user import FORMATION_M1, FORMATION_M2, formation_short

from . import (
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
)

User = get_user_model()


def get_users_roles_for_session(users, session) -> Mapping[User, str]:
    """
    Get the role (in short format) of each user of `users` in `session`.
    """
    user_session_chosen_as = dict(
        session.availability_statuses.exclude(chosen_as=CHOSEN_AS_NOT).values_list(
            "helper_id", "chosen_as"
        )
    )
    qualifications = session.qualifications.all()

    roles = {}
    for user in users:
        label = ""
        for quali in qualifications:
            if user == quali.leader:
                label = formation_short(FORMATION_M2, True)
                break
            elif user in quali.helpers.all():
                label = formation_short(FORMATION_M1, True)
                break
            elif user == quali.actor:
                # Translators: Nom court pour 'Intervenant'
                label = gettext("Int.")
                break
        # Vérifie tout de même si l’utilisateur est déjà sélectionné
        if not label and user.id in user_session_chosen_as:
            if user_session_chosen_as[user.id] == CHOSEN_AS_LEADER:
                label = formation_short(FORMATION_M2, True)
            elif user_session_chosen_as[user.id] == CHOSEN_AS_HELPER:
                label = formation_short(FORMATION_M1, True)
            elif user_session_chosen_as[user.id] == CHOSEN_AS_ACTOR:
                # Translators: Nom court pour 'Intervenant'
                label = gettext("Int.")
            elif user_session_chosen_as[user.id] == CHOSEN_AS_REPLACEMENT:
                # Translators: Nom court pour 'Moniteur de secours'
                label = gettext("S")
            else:
                label = gettext("×")

        if user == session.superleader:
            # Translators: Nom court pour 'Moniteur +'
            label = "{} / {}".format(label, gettext("M+")) if label else gettext("M+")

        roles[user] = label
    return roles


def is_morning(begin):
    return begin <= time(12, 00)


class GeneralSeason(object):
    def __init__(self, *, year, dv_season, seasons, helper_id=None):
        from calendar import monthrange

        self.year = year
        self.dv_season = dv_season
        self._seasons = seasons
        self.helper_id = helper_id
        self.pk = seasons[0].pk if seasons else None

        if dv_season == DV_SEASON_SPRING:
            self.begin = datetime.date(year, 1, 1)
            last_day = monthrange(year, DV_SEASON_LAST_SPRING_MONTH)[1]
            self.end = datetime.date(year, DV_SEASON_LAST_SPRING_MONTH, last_day)
            self.season_full = _("Printemps {year}").format(year=year)
        else:
            self.begin = datetime.date(year, DV_SEASON_LAST_SPRING_MONTH + 1, 1)
            self.end = datetime.date(year, 12, 31)
            self.season_full = _("Automne {year}").format(year=year)

        cantons = []
        for s in seasons:
            for c in s.cantons:
                if c not in cantons:
                    cantons.append(c)
        self._base_cantons = cantons
        self.cantons = list(cantons)

        self.state_icon = ""
        self.state_full = _("Planning général")

        self._sessions_with_q = None

    @property
    def sessions_with_qualifs(self):
        if self._sessions_with_q is None:
            Session = django_apps.get_model("challenge", "Session")
            qs = (
                Session.objects.filter(
                    orga__address_canton__in=self._base_cantons,
                    day__gte=self.begin,
                    day__lte=self.end,
                )
                .prefetch_related(
                    "availability_statuses",
                    "qualifications",
                    "qualifications__leader",
                    "qualifications__helpers",
                    "qualifications__actor",
                    "orga",
                )
                .annotate(Count("qualifications"))
                .filter(qualifications__count__gt=0)
                .order_by("day", "begin", "orga__name")
            )
            # If a helper is specified, restrict to sessions relevant to that helper
            if self.helper_id:
                qs = qs.filter(
                    Q(superleader_id=self.helper_id)
                    | (
                        Q(availability_statuses__helper_id=self.helper_id)
                        & ~Q(availability_statuses__chosen_as=CHOSEN_AS_NOT)
                    )
                    | Q(qualifications__leader_id=self.helper_id)
                    | Q(qualifications__helpers__id=self.helper_id)
                    | Q(qualifications__actor_id=self.helper_id)
                ).distinct()
                # Update cantons to only those with confirmed availability/assignment
                self.cantons = list(
                    qs.values_list("orga__address_canton", flat=True).distinct()
                )
            self._sessions_with_q = qs
        return self._sessions_with_q

    @property
    def work_wishes(self):
        # Aggregate work wishes across all seasons by helper
        HelperSeasonWorkWish = django_apps.get_model(
            "challenge", "HelperSeasonWorkWish"
        )
        return (
            HelperSeasonWorkWish.objects.filter(season__in=self._seasons)
            .values("helper_id")
            .annotate(amount=Sum("amount"))
        )

    def desc(self, abbr=False):
        from defivelo.templatetags.dv_filters import cantons_abbr

        cantons_str = ", ".join(cantons_abbr(self.cantons, abbr))
        return _("{cantons} - {season_full}").format(
            cantons=cantons_str, season_full=self.season_full
        )

    @property
    def desc_abbr(self):
        return self.desc(True)


def seasons_in_scope_for_user(user, year, dv_season):
    """
    Return queryset of seasons for a given user/year/dv_season using the same
    canton scoping as SeasonMixin/UserProfile.get_seasons.
    """
    qs = user.profile.get_seasons(False).filter(year=year)
    if dv_season == DV_SEASON_SPRING:
        qs = qs.filter(month_start__lte=DV_SEASON_LAST_SPRING_MONTH)
    elif dv_season == DV_SEASON_AUTUMN:
        qs = qs.filter(month_start__gt=DV_SEASON_LAST_SPRING_MONTH)
    else:
        qs = qs.none()
    return qs
