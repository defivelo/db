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
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from allauth.account import views as allauth_views
from allauth.account.adapter import DefaultAccountAdapter


class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class EmailView(allauth_views.EmailView):
    """
    allauth resends a confirmation even for a verified address, with a link that
    can only fail (confirmation keys only resolve unverified addresses).
    """

    def _action_send(self, request, *args, **kwargs):
        email_address = self._get_email_address(request)
        if email_address and email_address.verified:
            messages.info(
                request,
                _("L'adresse e-mail %(email)s est déjà vérifiée.")
                % {"email": email_address.email},
            )
            return None
        return super()._action_send(request, *args, **kwargs)
