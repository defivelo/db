# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

from django.utils.translation import ugettext_lazy as _

from memoize import memoize
from rolepermissions.checkers import has_permission as uncached_has_permission
from rolepermissions.roles import AbstractUserRole

from apps.common import DV_STATES


# Override 'has_permission' from rolepermissions to add memoization for performance reasons
@memoize()
def has_permission(user, permission_name):
    return uncached_has_permission(user, permission_name)


@memoize()
def user_cantons(user):
    """
    List of the cantons _managed_ by this user
    """
    if has_permission(user, "cantons_all"):
        return DV_STATES
    elif has_permission(user, "cantons_mine"):
        return [m.canton for m in user.managedstates.all()]
    else:
        raise LookupError("No user cantons")


class Collaborator(AbstractUserRole):
    """
    Moniteur 1, 2 ou Intervenant
    """

    available_permissions = {
        "challenge_see_all_orga": True,
        "user_view_list": True,
        "user_view_list_non_collaborator": False,
        "user_export_all_fields": False,
        "timesheet": True,
    }


class StateManager(AbstractUserRole):
    """
    Chargé de projet, responsable d’un ou plusieurs cantons
    """

    available_permissions = {
        "cantons_all": False,
        "cantons_mine": True,
        "user_view_list": True,
        "user_view_list_non_collaborator": True,
        "user_export_all_fields": True,
        "user_detail_other": True,
        "user_edit_other": True,
        "user_crud_dv_public_fields": True,
        "user_crud_dv_private_fields": True,
        "user_can_send_credentials": True,
        "user_create": True,
        "orga_detail_all": True,
        "orga_crud": True,
        "orga_edit_address": True,
        "orga_show": True,
        "orga_edit": True,
        "challenge_season_crud": True,
        "challenge_see_all_orga": True,
        "challenge_session_crud": True,
        "challenge_invoice_cru": True,
        "challenge_invoice_reset_to_draft": False,
        "challenge_season_see_state_planning": True,
        "settings_crud": True,
        "timesheet": True,
        "timesheet_editor": True,
        "registration_validate": True,
    }


class PowerUser(AbstractUserRole):
    """
    Bureau
    """

    available_permissions = {
        "cantons_all": True,
        "cantons_mine": True,
        "user_view_list": True,
        "user_view_list_non_collaborator": True,
        "user_export_all_fields": True,
        "user_detail_other": True,
        "user_edit_other": True,
        "user_create": True,
        "user_crud_dv_public_fields": True,
        "user_crud_dv_private_fields": True,
        "user_edit_employee_code": True,
        "user_can_send_credentials": True,
        "user_can_resend_credentials": True,
        "user_deletions": True,
        "user_set_role": True,
        "user_mark_inactive": True,
        "home_article_cud": True,
        "orga_detail_all": True,
        "orga_crud": True,
        "orga_edit_address": True,
        "orga_show": True,
        "orga_edit": True,
        "challenge_invoice_cru": True,
        "challenge_invoice_reset_to_draft": True,
        "challenge_see_all_orga": True,
        "challenge_session_crud": True,
        "challenge_season_crud": True,
        "challenge_season_see_state_planning": True,
        "settings_crud": True,
        "timesheet": True,
        "timesheet_control": True,
        "timesheet_editor": True,
    }


class Coordinator(AbstractUserRole):
    """
    Coordinateur d’établissement
    """

    available_permissions = {
        "home_without_articles": True,
        "orga_show": True,
        "orga_edit": True,
        "challenge_see_all_orga": False,
        "registration_create": True,
    }


DV_AVAILABLE_ROLES = (
    (None, _("Aucun rôle")),
    ("collaborator", _("Collabora·teur·trice")),
    ("state_manager", _("Chargé·e de projet")),
    ("coordinator", _("Coordina·teur·trice")),
    ("power_user", _("Bureau de coordination")),
)

DV_AUTOMATIC_ROLES = ["collaborator"]
