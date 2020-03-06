from django import forms
from django.db.models import Q
from django.forms import formset_factory
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models.session import Session
from apps.common.fields import CheckboxInput, NumberInput, TimeNumberInput
from apps.salary.models import Timesheet


class TimesheetFormBase(forms.ModelForm):
    class Meta:
        model = Timesheet
        readonly = ("date", "time_helper", "time_actor")
        fields = [
            "user",
            "date",
            "time_helper",
            "time_actor",
            "overtime",
            "traveltime",
            "comments",
        ]
        widgets = {
            "user": forms.HiddenInput(),
            "date": forms.HiddenInput(),
            "time_helper": TimeNumberInput(
                attrs={"readonly": "readonly", "class": "hide", "data-unit-price": 30},
            ),
            "time_actor": NumberInput(
                attrs={"readonly": "readonly", "class": "hide", "data-unit-price": 100},
            ),
            "overtime": TimeNumberInput(
                attrs={
                    "step": 0.25,
                    "min": -10,
                    "max": 10,
                    "class": "hide",
                    "data-unit-price": 30,
                }
            ),
            "traveltime": TimeNumberInput(
                attrs={
                    "step": 0.25,
                    "min": 0,
                    "max": 5,
                    "class": "hide",
                    "data-unit-price": 30,
                }
            ),
            "comments": forms.Textarea(attrs={"rows": 3, "cols": 20}),
        }

    def __init__(self, validator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator

    def _get_validation_exclusions(self):
        exclude = super()._get_validation_exclusions()
        exclude.append("user")
        return exclude

    def clean(self):
        cleaned_data = super().clean()
        if not (
            Session.objects.values("day")
            .filter(
                Q(qualifications__actor=cleaned_data["user"])
                | Q(qualifications__helpers=cleaned_data["user"])
                | Q(qualifications__leader=cleaned_data["user"])
            )
            .filter(day=cleaned_data["date"])
            .exists()
        ):
            raise forms.ValidationError(
                _("Vous ne pouver pas rentrer des heures pour le {day}.").format(
                    day=cleaned_data["date"]
                )
            )

        return cleaned_data

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
        if self.initial.get("validated"):
            for key in self.fields:
                self.fields[key].widget.attrs["readonly"] = True
                self.fields[key].disabled = True


class ControlTimesheetForm(TimesheetFormBase):
    validated = forms.BooleanField(
        label=_("Valider"), required=False, widget=CheckboxInput()
    )

    class Meta(TimesheetFormBase.Meta):
        fields = TimesheetFormBase.Meta.fields + ["validated"]

    def clean(self):
        cleaned_data = super().clean()
        if self.initial["validated"] and not cleaned_data.get("validated"):
            cleaned_data["validated_at"] = None
            cleaned_data["validated_by"] = None
        elif not self.initial["validated"] and cleaned_data.get("validated"):
            cleaned_data["validated_at"] = timezone.now()
            cleaned_data["validated_by"] = self.validator
        del cleaned_data["validated"]
        return cleaned_data


ControlTimesheetFormSet = formset_factory(ControlTimesheetForm, max_num=0, extra=0)
TimesheetFormSet = formset_factory(TimesheetForm, max_num=0, extra=0)
