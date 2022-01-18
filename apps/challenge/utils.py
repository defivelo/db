from datetime import time
from typing import Mapping

from django.contrib.auth import get_user_model
from django.utils.translation import gettext

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
