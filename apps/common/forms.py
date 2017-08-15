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

from bootstrap3_datetime.widgets import DateTimePicker
from django.forms import TimeField
from localflavor.generic.forms import DEFAULT_DATE_INPUT_FORMATS, DateField

SWISS_DATE_INPUT_FORMAT = '%d.%m.%Y'
SWISS_DATE_DISPLAY_FORMAT = 'DD.MM.YYYY'

SWISS_DATE_INPUT_FORMATS = \
    DEFAULT_DATE_INPUT_FORMATS + (SWISS_DATE_INPUT_FORMAT, )


class SwissDateField(DateField):
    """
    A date input field which uses the bootstrap widget for pickin a Date
    """
    def __init__(self, input_formats=None, *args, **kwargs):
        input_formats = input_formats or SWISS_DATE_INPUT_FORMATS
        super(DateField, self).__init__(
            input_formats=input_formats,
            widget=DateTimePicker(
                {'placeholder': SWISS_DATE_DISPLAY_FORMAT},
                options={
                    "format": SWISS_DATE_DISPLAY_FORMAT}),
            *args, **kwargs)


class SwissTimeField(TimeField):
    """
    A date input field which uses the bootstrap widget for pickin a Date
    """
    def __init__(self, *args, **kwargs):
        super(TimeField, self).__init__(
            widget=DateTimePicker({'placeholder': 'HH:mm'},
                                  icon_attrs={'class': 'glyphicon'},
                                  options={"format": "HH:mm",
                                           "minuteStepping": 15}),
            *args, **kwargs)
