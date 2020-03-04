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

from django.forms import ModelChoiceField, TimeField
from django.template.loader import render_to_string

from bootstrap3_datetime.widgets import DateTimePicker
from dal_select2.widgets import ModelSelect2
from django_countries import countries
from django_countries.fields import LazyTypedChoiceField
from django_countries.widgets import CountrySelectWidget
from localflavor.generic.forms import DEFAULT_DATE_INPUT_FORMATS, DateField
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

SWISS_DATE_INPUT_FORMAT = "%d.%m.%Y"
SWISS_DATE_DISPLAY_FORMAT = "DD.MM.YYYY"

SWISS_DATE_INPUT_FORMATS = DEFAULT_DATE_INPUT_FORMATS + (SWISS_DATE_INPUT_FORMAT,)


class SwissDateField(DateField):
    """
    A date input field which uses the bootstrap widget for pickin a Date
    """

    def __init__(self, input_formats=None, *args, **kwargs):
        input_formats = input_formats or SWISS_DATE_INPUT_FORMATS
        super(DateField, self).__init__(
            input_formats=input_formats,
            widget=DateTimePicker(
                {"placeholder": SWISS_DATE_DISPLAY_FORMAT},
                options={"format": SWISS_DATE_DISPLAY_FORMAT},
            ),
            *args,
            **kwargs,
        )


class SwissTimeInput(DateTimePicker):
    format = "HH:mm"

    def __init__(self, attrs={}, *args, **kwargs):
        attrs["placeholder"] = "HH:mm"
        super().__init__(
            attrs,
            icon_attrs={"class": "glyphicon glyphicon-time"},
            options={"format": "HH:mm", "stepping": 15},
            *args,
            **kwargs,
        )


class SwissTimeField(TimeField):
    """
    A date input field which uses the bootstrap widget for pickin a Date
    """

    def __init__(self, *args, **kwargs):
        super(TimeField, self).__init__(
            widget=SwissTimeInput, *args, **kwargs,
        )


class CHPhoneNumberField(PhoneNumberField):
    """
    A PhoneNumberField that uses the national fallback widget
    """

    def __init__(self, *args, **kwargs):
        super(CHPhoneNumberField, self).__init__(
            widget=PhoneNumberInternationalFallbackWidget, *args, **kwargs
        )


class BS3CountriesField(LazyTypedChoiceField):
    """
    A Bootstrap3 Countries selection Field
    """

    def __init__(self, *args, **kwargs):
        super(BS3CountriesField, self).__init__(
            widget=CountrySelectWidget(
                layout=render_to_string("country_select_widget.html")
            ),
            choices=countries,
            initial="CH",
            *args,
            **kwargs,
        )


class UserAutoComplete(ModelChoiceField):
    """
    A User input field which uses the Autocmplete URL and has the good
    default widget
    """

    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url", False)
        super(UserAutoComplete, self).__init__(
            widget=ModelSelect2(url=url), *args, **kwargs
        )

    def label_from_instance(self, obj):
        return obj.get_full_name()
