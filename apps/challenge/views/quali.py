# -*- coding: utf-8 -*-
#
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
from __future__ import unicode_literals

from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from ..forms import QualificationForm
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
        form_kwargs = super(QualiMixin, self).get_form_kwargs()
        try:
            form_kwargs["session"] = Session.objects.get(pk=self.get_session_pk())
        except Exception:
            pass
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(QualiMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context["menu_category"] += " qualification"
        try:
            context["session"] = Session.objects.get(pk=self.get_session_pk())
        except Exception:
            pass
        try:
            context["season"] = self.season
        except Exception:
            pass
        return context


class QualiCreateView(QualiMixin, SuccessMessageMixin, CreateView):
    success_message = _("Qualif' créée")

    def get_initial(self):
        return {"session": self.get_session_pk()}


class QualiUpdateView(QualiMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Qualif' mise à jour")


class QualiDeleteView(QualiMixin, DeleteView):
    success_message = _("Qualif' supprimée")
