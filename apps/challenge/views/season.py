# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016 Didier Raboud <me+defivelo@odyx.org>
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

import operator
from collections import OrderedDict
from functools import reduce

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import date, time
from django.utils.translation import ugettext as u, ugettext_lazy as _
from django.views.generic.dates import YearArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from import_export.formats import base_formats
from rolepermissions.mixins import HasPermissionsMixin
from tablib import Dataset

from apps.user.models import FORMATION_M2
from apps.user.views import ActorsList, HelpersList
from defivelo.roles import user_cantons
from defivelo.views import MenuView

from .. import AVAILABILITY_FIELDKEY, MAX_MONO1_PER_QUALI, STAFF_FIELDKEY
from ..forms import (
    SeasonAvailabilityForm, SeasonForm, SeasonNewHelperAvailabilityForm,
    SeasonStaffChoiceForm,
)
from ..models import HelperSessionAvailability, Season
from .mixins import CantonSeasonFormMixin


class SeasonMixin(CantonSeasonFormMixin, HasPermissionsMixin, MenuView):
    required_permission = 'challenge_season_crud'
    model = Season
    context_object_name = 'season'
    form_class = SeasonForm

    def get_context_data(self, **kwargs):
        context = super(SeasonMixin, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'season'
        context['season'] = self.season
        return context

    def get_queryset(self):
        qs = super(SeasonMixin, self).get_queryset()
        usercantons = user_cantons(self.request.user)
        if self.model == Season and usercantons:
            cantons = [
                    Q(cantons__contains=state)
                    for state in user_cantons(self.request.user)
                ]
            qs = qs.filter(reduce(operator.or_, cantons))
        if self.model == get_user_model() and usercantons:
            # Check that the intersection isn't empty
            cantons = list(
                set(usercantons)
                .intersection(set(self.season.cantons))
            )
            if not cantons:
                raise PermissionDenied
        return qs


class SeasonListView(SeasonMixin, YearArchiveView):
    date_field = 'begin'
    allow_empty = True
    allow_future = True
    context_object_name = 'seasons'
    make_object_list = True


class SeasonDetailView(SeasonMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super(SeasonDetailView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-detail'
        return context


class SeasonUpdateView(SeasonMixin, SuccessMessageMixin, UpdateView):
    success_message = _("Saison mise à jour")


class SeasonAvailabilityMixin(SeasonMixin):
    def potential_helpers(self, queryset=None):
        if not queryset:
            queryset = get_user_model().objects

            # Pick the one helper from the command line if it makes sense
            resolvermatch = self.request.resolver_match
            if 'helperpk' in resolvermatch.kwargs:
                queryset = queryset.filter(
                    pk=int(resolvermatch.kwargs['helperpk'])
                )

        all_helpers = queryset.order_by('first_name', 'last_name')
        return (
            (_('Moniteurs 2'), all_helpers.filter(profile__formation='M2')),
            (_('Moniteurs 1'), all_helpers.filter(profile__formation='M1')),
            (_('Intervenants'), all_helpers.exclude(
                profile__actor_for__isnull=True
            )),
        )

    def current_availabilities(self):
        return (
            HelperSessionAvailability.objects
            .filter(session__in=self.object.sessions_with_qualifs)
            .prefetch_related('helper')
        )

    def get_initial(self, all_hsas=None, all_helpers=None):
        initials = OrderedDict()
        if not all_hsas:
            all_hsas = self.current_availabilities()
        if not all_helpers:
            all_helpers = self.potential_helpers()

        if all_hsas:
            for helper_category, helpers in all_helpers:
                for helper in helpers:
                    helper_availability = {
                        a.session_id: a for a in all_hsas
                        if a.helper == helper
                    }
                    for session in self.object.sessions_with_qualifs:
                        fieldkey = AVAILABILITY_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk)
                        staffkey = STAFF_FIELDKEY.format(
                            hpk=helper.pk, spk=session.pk)
                        try:
                            hsa = helper_availability[session.id]
                            initials[fieldkey] = hsa.availability
                            if hsa.chosen:
                                initials[staffkey] = \
                                    session.user_assignment(helper)
                            else:
                                initials[staffkey] = ''
                        except:
                            initials[fieldkey] = ''
                            initials[staffkey] = ''
            return initials

    def get_context_data(self, **kwargs):
        context = \
            super(SeasonAvailabilityMixin, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-availability'
        return context


class SeasonExportView(SeasonAvailabilityMixin, DetailView):
    def render_to_response(self, context, **response_kwargs):
        resolvermatch = self.request.resolver_match
        formattxt = resolvermatch.kwargs.get('format', 'csv')
        # Instantiate the format object from base_formats in import_export
        try:
            format = getattr(base_formats, formattxt.upper())()
        except AttributeError:
            format = base_formats.CSV()

        filename = (
            _('DV-Saison-{cantons}-{YM_startdate}.{extension}').format(
                cantons='-'.join(self.season.cantons),
                YM_startdate=self.season.begin.strftime('%Y%m'),
                extension=format.get_extension()
            )
        )
        dataset = Dataset()
        # Prépare le fichier
        dataset.append_col([
            u('Date'),
            u('Canton'),
            u('Établissement'),
            u('Emplacement'),
            u('Heures'),
            u('Qualifs'),
            u('Prénom & Nom'),
        ])
        for session in self.season.sessions_with_qualifs:
            dataset.append_col([
                date(session.day),
                session.organization.address_canton,
                session.organization.name,
                session.address_city if session.address_city
                else session.organization.address_city,
                '%s - %s' % (time(session.begin), time(session.end)),
                session.n_qualifications,
                ''
            ])
        dataset.insert_separator(6, u('Présences des moniteurs'))

        response = HttpResponse(getattr(dataset, formattxt),
                                format.get_content_type() + ';charset=utf-8')
        response['Content-Disposition'] = \
            'attachment; filename="%s"' % filename
        return response


class SeasonAvailabilityView(SeasonAvailabilityMixin, DetailView):
    template_name = 'challenge/season_availability.html'

    def get_context_data(self, **kwargs):
        context = \
            super(SeasonAvailabilityView, self).get_context_data(**kwargs)
        # Add the form for picking a new helper
        context['form'] = SeasonNewHelperAvailabilityForm()
        hsas = self.current_availabilities()
        if hsas:
            # Fill in the helpers with the ones we currently have
            helpers = {hsa.helper.pk: hsa.helper.pk for hsa in hsas}
            potential_helpers = self.potential_helpers(
                queryset=get_user_model().objects.filter(pk__in=helpers)
            )

            context['potential_helpers'] = potential_helpers
            context['availabilities'] = self.get_initial(
                all_hsas=hsas,
                all_helpers=potential_helpers
            )
        return context

    def post(self, request, *args, **kwargs):
        seasonpk = kwargs.get('pk', None)
        form = SeasonNewHelperAvailabilityForm(request.POST)
        if form.is_valid():
            helperpk = int(form.cleaned_data['helper'])
            return HttpResponseRedirect(
                reverse_lazy('season-availabilities-update',
                             kwargs={'pk': seasonpk, 'helperpk': helperpk})
            )
        return HttpResponseRedirect(
            reverse_lazy('season-availabilities', kwargs={'pk': seasonpk})
        )


class SeasonAvailabilityUpdateView(SeasonAvailabilityMixin, SeasonUpdateView):
    template_name = 'challenge/season_availability_update.html'
    success_message = _("Disponibilités mises à jour")
    form_class = SeasonAvailabilityForm

    def get_form_kwargs(self):
        form_kwargs = \
            super(SeasonAvailabilityMixin, self).get_form_kwargs()
        form_kwargs['potential_helpers'] = self.potential_helpers()
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = \
            super(SeasonAvailabilityMixin, self).get_context_data(**kwargs)
        context['potential_helpers'] = self.potential_helpers()
        return context

    def form_valid(self, form):
        # Create or update the Availability objects
        for session in self.object.sessions_with_qualifs:
            for helper_category, helpers in self.potential_helpers():
                for helper in helpers:
                    fieldkey = AVAILABILITY_FIELDKEY.format(hpk=helper.pk,
                                                            spk=session.pk)
                    if fieldkey in form.cleaned_data:
                        availability = form.cleaned_data[fieldkey]
                        if availability:
                            (hsa, created) = (
                                HelperSessionAvailability.objects
                                .get_or_create(
                                    session=session,
                                    helper=helper,
                                    defaults={'availability': availability})
                                )
                            if not created:
                                hsa.availability = availability
                                hsa.save()
        return HttpResponseRedirect(
            reverse_lazy('season-availabilities',
                         kwargs={'pk': self.object.pk}))


class SeasonStaffChoiceUpdateView(SeasonAvailabilityMixin, SeasonUpdateView):
    template_name = 'challenge/season_staff_update.html'
    success_message = _("Choix du personnel mises à jour")
    form_class = SeasonStaffChoiceForm

    def available_helpers(self):
        if hasattr(self, 'ahelpers'):
            return self.ahelpers
        # Only take available people
        hsas = self.current_availabilities().exclude(availability='n')
        if hsas:
            # Fill in the helpers with the ones we currently have
            helpers = {hsa.helper.pk: hsa.helper.pk for hsa in hsas}
            self.ahelpers = self.potential_helpers(
                queryset=get_user_model().objects.filter(pk__in=helpers)
            )
            return self.ahelpers

    def get_form_kwargs(self):
        form_kwargs = \
            super(SeasonStaffChoiceUpdateView, self).get_form_kwargs()
        form_kwargs['available_helpers'] = self.available_helpers()
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = \
            super(SeasonStaffChoiceUpdateView, self).get_context_data(**kwargs)
        context['available_helpers'] = self.available_helpers()
        return context

    def form_valid(self, form):
        # Update all staff choices
        for session in self.object.sessions_with_qualifs:
            session_helpers = {}  # Those picked for the season
            session_non_helpers = {}  # Those not picked for the season
            for helper_category, helpers in self.available_helpers():
                for helper in helpers:
                    fieldkey = STAFF_FIELDKEY.format(hpk=helper.pk,
                                                     spk=session.pk)
                    try:
                        HelperSessionAvailability.objects.filter(
                                session=session,
                                helper=helper
                            ).update(chosen=form.cleaned_data[fieldkey])
                        if form.cleaned_data[fieldkey]:
                            session_helpers[helper.pk] = helper
                        else:
                            session_non_helpers[helper.pk] = helper
                    # if the fieldkey's not in cleaned_data, or other reasons
                    except:
                        pass

            # Do a session-wide check across all helpers picked for that
            # session
            n_qualifs = session.qualifications.count()
            for quali in session.qualifications.all():
                for non_helper in session_non_helpers.values():
                    # Drop those not in the session anymore
                    if non_helper == quali.leader:
                        quali.leader = None
                    if non_helper in quali.helpers.all():
                        quali.helpers.remove(helper)
                    if non_helper == quali.actor:
                        quali.actor = None
                if n_qualifs == 1:
                    for helper in session_helpers.values():
                        if (
                            helper.profile.formation == FORMATION_M2 and
                            quali.leader is None
                        ):
                            quali.leader = helper
                            try:
                                quali.helpers.remove(helper)
                            except:
                                pass
                        elif (
                            helper.profile.formation is not None and
                            quali.helpers.count() < MAX_MONO1_PER_QUALI
                        ):
                            quali.helpers.add(helper)
                            if quali.leader == helper:
                                quali.leader = None
                        elif (
                            helper.profile.actor_for is not None and
                            quali.actor is None
                        ):
                            quali.actor = helper
                quali.save()
        return HttpResponseRedirect(
            reverse_lazy('season-availabilities',
                         kwargs={'pk': self.object.pk}))


class SeasonCreateView(SeasonMixin, SuccessMessageMixin, CreateView):
    success_message = _("Saison créée")


class SeasonDeleteView(SeasonMixin, SuccessMessageMixin, DeleteView):
    success_message = _("Saison supprimée")
    success_url = reverse_lazy('season-list')


class SeasonHelperListView(HelpersList, SeasonMixin):
    model = get_user_model()
    page_title = _('Moniteurs de la saison')

    def get_context_data(self, **kwargs):
        context = super(SeasonHelperListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-helperlist'
        return context

    def get_queryset(self):
        return (
            super(SeasonHelperListView, self).get_queryset()
            .filter(
                availabilities__session__in=self.season.sessions_with_qualifs,
                availabilities__chosen=True
            )
            .distinct()
        )


class SeasonActorListView(ActorsList, SeasonMixin):
    model = get_user_model()
    page_title = _('Intervenants de la saison')

    def get_context_data(self, **kwargs):
        context = super(SeasonActorListView, self).get_context_data(**kwargs)
        # Add our submenu_category context
        context['submenu_category'] = 'season-actorslist'
        return context

    def get_queryset(self):
        return (
            super(SeasonActorListView, self).get_queryset()
            .filter(
                availabilities__session__in=self.season.sessions_with_qualifs,
                availabilities__chosen=True
            )
            .distinct()
        )
