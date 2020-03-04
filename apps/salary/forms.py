from django import forms
from django.forms import formset_factory
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.common.forms import SwissTimeInput
from apps.salary.fields import CheckboxInput, TimeNumberInput
from apps.salary.models import Timesheet


class TimesheetFormBase(forms.ModelForm):
    class Meta:
        model = Timesheet
        readonly = ("date", "time_monitor", "time_actor")
        fields = [
            "user",
            "date",
            "time_monitor",
            "time_actor",
            "overtime",
            "traveltime",
            "comments"
        ]
        widgets = {
            "user": forms.HiddenInput(),
            "date": forms.HiddenInput(),
            "time_monitor": SwissTimeInput(
                attrs={"readonly": "readonly"}, format="HH:mm"
            ),
            "time_actor": SwissTimeInput(
                attrs={"readonly": "readonly"}, format="HH:mm"
            ),
            "overtime": TimeNumberInput(attrs={"step": 0.25, "min": -10, "max": 10}),
            "traveltime": TimeNumberInput(attrs={"step": 0.25, "min": 0, "max": 5}),
        }

    def __init__(self, validator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator
    def _get_validation_exclusions(self):
        exclude = super()._get_validation_exclusions()
        exclude.append("user")
        return exclude

    def save(self):
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate."
                % (
                    self.instance._meta.object_name,
                    "created" if self.instance._state.adding else "changed",
                )
            )
        timesheet, created = Timesheet.objects.update_or_create(
            user=self.cleaned_data["user"],
            date=self.cleaned_data["date"],
            defaults=self.cleaned_data,
        )
        return timesheet

class TimesheetForm(TimesheetFormBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('validate'):
            for key in self.fields:
                self.fields[key].widget.attrs['readonly'] = True

class ControlTimesheetForm(TimesheetFormBase):
    validate = forms.BooleanField(label=_("Valider"), required=False, widget=CheckboxInput())

    class Meta(TimesheetForm.Meta):
        fields = TimesheetForm.Meta.fields + ['validate']

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('validate'):
            cleaned_data['validated_at'] = None
            cleaned_data['validated_by'] = None
        elif not self.initial['validate']:
            cleaned_data['validated_at'] = timezone.now
            cleaned_data['validated_by'] = self.validator
        del cleaned_data['validate']
        return cleaned_data


ControlTimesheetFormSet = formset_factory(ControlTimesheetForm, max_num=0, extra=0)
TimesheetFormSet = formset_factory(TimesheetForm, max_num=0, extra=0)
