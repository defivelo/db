# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015,2020 Didier Raboud <didier.raboud@liip.ch>
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

from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from defivelo.roles import has_permission

from ..forms import QualificationDeleteForm, QualificationForm
from ..models import Qualification, Session
from .session import SessionMixin


class QualiMixin(SessionMixin):
    model = Qualification
    context_object_name = "qualification"
    form_class = QualificationForm
    view_does_crud = True

    def get_session_pk(self):
        resolvermatch = self.request.resolver_match
        if "sessionpk" in resolvermatch.kwargs:
            return int(resolvermatch.kwargs["sessionpk"])

    def get_season_pk(self):
        resolvermatch = self.request.resolver_match
        if "seasonpk" in resolvermatch.kwargs:
            return int(resolvermatch.kwargs["seasonpk"])

    def get_success_url(self):
        return reverse_lazy(
            "session-detail",
            kwargs={"seasonpk": self.get_season_pk(), "pk": self.get_session_pk()},
        )

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        try:
            session = Session.objects.get(pk=self.get_session_pk())
            form_kwargs["session"] = session
            # Coordinator without StateManager rights
            form_kwargs["is_for_coordinator"] = (
                not has_permission(self.request.user, "challenge_session_crud")
                and self.request.user == session.orga.coordinator
            )
        except Exception:
            pass
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] += " qualification"
        try:
            context["session"] = Session.objects.get(pk=self.get_session_pk())
        except Exception:
            pass
        context["season"] = self.season_object
        context["qualification_user_errors"] = self.get_object().user_errors(
            self.request.user
        )
        return context


class QualiCreateView(QualiMixin, SuccessMessageMixin, CreateView):
    success_message = _("Qualif’ créée")

    def get_initial(self):
        return {"session": self.get_session_pk()}

    def dispatch(self, *args, **kwargs):
        """
        Quali Creation is only for StateManagers, not coordinators
        """
        if not has_permission(self.request.user, "challenge_session_crud"):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)


class QualiUpdateView(QualiMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Qualif’ mise à jour")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timesheets"] = self.object.get_related_timesheets().distinct()
        return context


class QualiDeleteView(QualiMixin, DeleteView):
    success_message = _("Qualif’ supprimée")
    form_class = QualificationDeleteForm

    def dispatch(self, *args, **kwargs):
        """
        Quali Deletion is only for StateManagers, not coordinators
        """
        if not has_permission(self.request.user, "challenge_session_crud"):
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timesheets"] = self.object.get_related_timesheets().distinct()
        return context

    def get_form_kwargs(self):
        # Cleanup unused kwargs genereated by QualiMixin
        return {
            k: v
            for (k, v) in super().get_form_kwargs().items()
            if k not in ["season", "cantons", "session", "is_for_coordinator"]
        }

    def form_valid(self, *args, **kwargs):
        self.get_object().get_related_timesheets().delete()
        return super().form_valid(*args, **kwargs)
