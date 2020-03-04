import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import widgets
from django.utils.dateparse import parse_duration
from django.utils.translation import ugettext_lazy as _


class DurationFieldForm(forms.FloatField):
    def prepare_value(self, value):
        if not isinstance(value, datetime.timedelta):
            value = datetime.timedelta(hours=value)
        return value

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, float):
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
