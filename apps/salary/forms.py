from django import forms
from django.db.models import Q
from django.forms import formset_factory
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rolepermissions.checkers import has_role

from apps.challenge.models.session import Session
from apps.common.fields import CheckboxInput, NumberInput, TimeNumberInput
from apps.salary.models import Timesheet

from . import HOURLY_RATE_ACTOR, HOURLY_RATE_HELPER


class TimesheetFormBase(forms.ModelForm):
    class Meta:
        model = Timesheet
        readonly = ("date", "time_helper", "time_actor")
        fields = [
            "date",
            "time_helper",
            "time_actor",
            "overtime",
            "traveltime",
            "comments",
        ]
        widgets = {
            "date": forms.HiddenInput(),
            "time_helper": TimeNumberInput(
                attrs={
                    "readonly": "readonly",
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_HELPER,
                },
            ),
            "time_actor": NumberInput(
                attrs={
                    "readonly": "readonly",
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_ACTOR,
                },
            ),
            "overtime": TimeNumberInput(
                attrs={
                    "step": 0.25,
                    "min": -10,
                    "max": 10,
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_HELPER,
                }
            ),
            "traveltime": TimeNumberInput(
                attrs={
                    "step": 0.25,
                    "min": 0,
                    "max": 5,
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_HELPER,
                }
            ),
            "comments": forms.Textarea(attrs={"rows": 3, "cols": 20}),
        }

    def __init__(self, selected_user, validator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator
        self.selected_user = selected_user

    def clean(self):
        cleaned_data = super().clean()
        if not (
            Session.objects.values("day")
            .filter(
                Q(qualifications__actor=self.selected_user)
                | Q(qualifications__helpers=self.selected_user)
                | Q(qualifications__leader=self.selected_user)
            )
            .filter(day=cleaned_data["date"])
            .exists()
        ):
            raise forms.ValidationError(
                _(
                    "Vous ne pouvez pas rentrer des heures pour le {day}: aucune qualif ce jour-ci."
                ).format(day=cleaned_data["date"])
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
            user=self.selected_user,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get("validated") and not has_role(self.validator, "power_user"):
            for key in self.fields:
                self.fields[key].widget.attrs["readonly"] = True
                self.fields[key].disabled = True

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
