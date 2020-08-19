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
from __future__ import unicode_literals

from django.forms import Form as DjangoEmptyForm
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from rolepermissions.mixins import HasPermissionsMixin

from .. import FORMATION_KEYS
from ..models import (
    USERSTATUS_ACTIVE,
    USERSTATUS_INACTIVE,
    USERSTATUS_RESERVE,
    UserProfile,
)


class MarkInactive(HasPermissionsMixin, FormView):
    template_name = "actions/mark_inactive.html"
    success_message = _("Tous les moniteurs ont été marqués inactifs.")
    success_url = reverse_lazy("user-list")
    form_class = DjangoEmptyForm
    required_permission = "user_mark_inactive"

    def get_affected_accounts(self):
        # Rend inactifs
        return (
            UserProfile.objects
            # … tous les moniteurs actifs ou réserve
            .filter(
                formation__in=FORMATION_KEYS,
                status__in=[USERSTATUS_ACTIVE, USERSTATUS_RESERVE,],
            )
            # … qui n'ont pas de rôles
            .exclude(user__groups__isnull=False)
            .order_by("user__first_name", "user__last_name")
            .prefetch_related("user")
        )

    def get_context_data(self, **kwargs):
        context = super(MarkInactive, self).get_context_data(**kwargs)
        context["affected_accounts"] = self.get_affected_accounts()
        return context

    def form_valid(self, form):
        # Proceed
        self.get_affected_accounts().update(
            status=USERSTATUS_INACTIVE, status_updatetime=timezone.now()
        )
        return super(MarkInactive, self).form_valid(form)
