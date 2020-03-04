import datetime
import numbers

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import widgets
from django.utils.dateparse import parse_duration
from django.utils.translation import ugettext_lazy as _


class DurationFieldForm(forms.FloatField):
    def prepare_value(self, value):
        if isinstance(value, datetime.timedelta):
            return value
        if isinstance(value, numbers.Number):
            return datetime.timedelta(hours=value)
        try:
            parsed = parse_duration(value)
        except ValueError:
            pass
        else:
            return parsed
        return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, numbers.Number):
            return value
        if isinstance(value, datetime.timedelta):
            return value.total_seconds() / 60 / 60
        try:
            parsed = parse_duration(value)
        except ValueError:
            pass
        else:
            if parsed is not None:
                return parsed.total_seconds() / 60 / 60

        raise ValidationError(
            self.error_messages["invalid"], code="invalid", params={"value": value},
        )


class DurationField(models.FloatField):
    def to_python(self, value):
        if isinstance(value, datetime.timedelta):
            return value.total_seconds() / 60 / 60
        return super().to_python(value)

    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": DurationFieldForm, **kwargs,})


class TimeNumberInput(widgets.NumberInput):
    input_type = "number"
    template_name = "django/forms/widgets/number.html"


# overide to make compatible with bootstrap
class CheckboxInput(widgets.Input):
    input_type = 'checkbox'
    template_name = 'django/forms/widgets/checkbox.html'

    def __init__(self, attrs=None, check_test=None):
        super().__init__(attrs)
        # check_test is a callable that takes a value and returns True
        # if the checkbox should be checked for that value.
        self.check_test = widgets.boolean_check if check_test is None else check_test

    def format_value(self, value):
        """Only return the 'value' attribute if value isn't empty."""
        if value is True or value is False or value is None or value == '':
            return
        return str(value)

    def get_context(self, name, value, attrs):
        if self.check_test(value):
            attrs = {**(attrs or {}), 'checked': True}
        return super().get_context(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if name not in data:
            # A missing value means False because HTML form submission does not
            # send results for unselected checkboxes.
            return False
        value = data.get(name)
        # Translate true and false strings to boolean values.
        values = {'true': True, 'false': False}
        if isinstance(value, str):
            value = values.get(value.lower(), value)
        return bool(value)

    def value_omitted_from_data(self, data, files, name):
        # HTML checkboxes don't appear in POST data if not checked, so it's
        # never known if the value is actually omitted.
        return False
