# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
# Copyright (C) 2020 Didier Raboud <didier.raboud@liip.ch>
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
from .quali import QualiCreateView, QualiDeleteView, QualiUpdateView
from .season import (
    SeasonActorListView,
    SeasonAvailabilityUpdateView,
    SeasonAvailabilityView,
    SeasonCreateView,
    SeasonDeleteView,
    SeasonDetailView,
    SeasonErrorsListView,
    SeasonExportView,
    SeasonHelperListView,
    SeasonListView,
    SeasonPlanningExportView,
    SeasonStaffChoiceUpdateView,
    SeasonUpdateView,
)
from .session import (
    SessionCreateView,
    SessionDeleteView,
    SessionDetailView,
    SessionExportView,
    SessionsListView,
    SessionStaffChoiceView,
    SessionUpdateView,
)
from .settings import AnnualStateSettingCreateView, AnnualStateSettingsListView
