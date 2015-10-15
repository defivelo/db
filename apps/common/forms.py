# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import TimeField

from bootstrap3_datetime.widgets import DateTimePicker
from localflavor.generic.forms import DEFAULT_DATE_INPUT_FORMATS, DateField

SWISS_DATE_INPUT_FORMAT = '%d.%m.%Y'
SWISS_DATE_DISPLAY_FORMAT = 'DD.MM.YYYY'

SWISS_DATE_INPUT_FORMATS = DEFAULT_DATE_INPUT_FORMATS + (SWISS_DATE_INPUT_FORMAT, )


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
                    "format": SWISS_DATE_DISPLAY_FORMAT,
                    "pickTime": False}),
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
                                           "pickDate": False,
                                           "minuteStepping": 15}),
            *args, **kwargs)
