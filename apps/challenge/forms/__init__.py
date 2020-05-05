# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
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

from .invoices import InvoiceForm, InvoiceFormQuick
from .qualification import QualificationForm, QualificationFormQuick
from .season import (
    SeasonAvailabilityForm,
    SeasonForm,
    SeasonNewHelperAvailabilityForm,
    SeasonStaffChoiceForm,
    SeasonToSpecificStateForm,
)
from .session import SessionForm
from .settings import AnnualStateSettingForm