from django import forms
from django.contrib.postgres.fields import ArrayField
from django.forms import widgets


class TimeNumberInput(widgets.NumberInput):
    input_type = "number"
    template_name = "forms/widgets/timenumber.html"


class NumberInput(widgets.NumberInput):
    input_type = "number"
    template_name = "forms/widgets/number.html"


# overide to make compatible with bootstrap
class CheckboxInput(widgets.Input):
    input_type = "checkbox"
    template_name = "django/forms/widgets/checkbox.html"

    def __init__(self, attrs=None, check_test=None):
        super().__init__(attrs)
        # check_test is a callable that takes a value and returns True
        # if the checkbox should be checked for that value.
        self.check_test = widgets.boolean_check if check_test is None else check_test

    def format_value(self, value):
        """Only return the 'value' attribute if value isn't empty."""
        if value is True or value is False or value is None or value == "":
            return
        return str(value)

    def get_context(self, name, value, attrs):
        if self.check_test(value):
            attrs = {**(attrs or {}), "checked": True}
        if "class" in attrs:
            attrs["class"] = attrs["class"].replace("form-control", "").strip()
        return super().get_context(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if name not in data:
            # A missing value means False because HTML form submission does not
            # send results for unselected checkboxes.
            return False
        value = data.get(name)
        # Translate true and false strings to boolean values.
        values = {"true": True, "false": False}
        if isinstance(value, str):
            value = values.get(value.lower(), value)
        return bool(value)

    def value_omitted_from_data(self, data, files, name):
        # HTML checkboxes don't appear in POST data if not checked, so it's
        # never known if the value is actually omitted.
        return False


class CheckboxMultipleChoiceField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.
    Uses Django's Postgres ArrayField
    and a MultipleChoiceField for its formfield.
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": CheckboxMultipleChoiceField,
            "choices": self.base_field.choices,
        }

        defaults.update(kwargs)
        # Skip the parent's formfield implementation completely as it does not matter.
        return super(ArrayField, self).formfield(**defaults)
