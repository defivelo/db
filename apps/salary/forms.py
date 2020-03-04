from django import forms
from django.forms import formset_factory

from apps.common.forms import SwissTimeInput
from apps.salary.models import Timesheet
from apps.salary.fields import TimeNumberInput


class TimesheetForm(forms.ModelForm):
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


TimesheetFormSet = formset_factory(TimesheetForm, max_num=0, extra=0)
