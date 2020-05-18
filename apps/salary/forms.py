from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import formset_factory
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from rolepermissions.checkers import has_role

from apps.challenge.models.session import Session
from apps.common.fields import CheckboxInput, NumberInput, TimeNumberInput
from apps.salary.models import (
    MonthlyCantonalValidation,
    Timesheet,
    MonthlyCantonalValidationUrl,
)

from . import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR


class TimesheetFormBase(forms.ModelForm):
    class Meta:
        model = Timesheet
        readonly = ("date", "time_helper", "actor_count", "leader_count")
        fields = [
            "date",
            "time_helper",
            "actor_count",
            "leader_count",
            "overtime",
            "traveltime",
            "comments",
        ]
        labels = {
            "time_helper": _("Heures moni·teur·trice (%(price)s.-/h)")
            % dict(price=HOURLY_RATE_HELPER),
            "actor_count": _("Intervention(s) (%(price)s.-/Qualif')")
            % dict(price=RATE_ACTOR),
            "leader_count": _("Participation(s) comme moniteur 2 (%(price)s.-/Qualif')")
            % dict(price=BONUS_LEADER),
            "overtime": _("Heures supplémentaires (%(price)s.-/h)")
            % dict(price=HOURLY_RATE_HELPER),
            "traveltime": _("Heures de trajet (cf. règlement)"),
        }
        widgets = {
            "date": forms.HiddenInput(),
            "time_helper": TimeNumberInput(
                attrs={
                    "readonly": "readonly",
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_HELPER,
                },
            ),
            "actor_count": NumberInput(
                attrs={
                    "readonly": "readonly",
                    "class": "hide",
                    "data-unit-price": RATE_ACTOR,
                },
            ),
            "leader_count": NumberInput(
                attrs={
                    "readonly": "readonly",
                    "class": "hide",
                    "data-unit-price": BONUS_LEADER,
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
                    "step": 0.5,
                    "min": 0,
                    "max": 1,
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


class MonthlyCantonalValidationForm(forms.ModelForm):
    validated = forms.BooleanField(
        label=_("Valider"), required=False, widget=CheckboxInput()
    )

    class Meta:
        model = MonthlyCantonalValidation
        fields = ["validated"]

    def __init__(self, validator, urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator
        # Add the urls as checkboxes, but first; so:
        # Store away the fields
        fields = self.fields.copy()
        # Empty it
        self.fields = {}
        for url in urls:
            self.fields[f"url_{url.pk}"] = forms.BooleanField(
                label=url.name,
                required=False,
                widget=CheckboxInput,
                help_text=mark_safe(
                    f'<a href="{url.url}" target="_blank">{url.url}</a>'
                ),
            )
        # Refill it
        for k, v in fields.items():
            self.fields[k] = v
        if self.initial.get("validated"):
            for key in self.fields:
                self.fields[key].widget.attrs["readonly"] = True
                self.fields[key].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        if self.initial["validated"] and not cleaned_data.get("validated"):
            cleaned_data["validated_at"] = None
            cleaned_data["validated_by"] = None
        elif not self.initial["validated"] and cleaned_data.get("validated"):
            # Verify that all URLs are ticked
            all_urls_ticked = True
            for k, v in self.fields.items():
                if k.startswith("url_"):
                    if not cleaned_data.get(k):
                        self.add_error(
                            k,
                            ValidationError(
                                _("Toutes les URLs doivent être vérifiées")
                            ),
                        )
                        all_urls_ticked = False
            if all_urls_ticked:
                cleaned_data["validated_at"] = timezone.now()
                cleaned_data["validated_by"] = self.validator
        del cleaned_data["validated"]
        return cleaned_data

    def save(self, commit=True):
        for val in ["validated_at", "validated_by"]:
            try:
                setattr(self.instance, val, self.cleaned_data[val])
            except KeyError:
                pass
        for k, v in self.fields.items():
            if k.startswith("url_"):
                pk = int(k.split("_")[1])
                self.instance.validated_urls.add(
                    MonthlyCantonalValidationUrl.objects.get(pk=pk)
                )
        return super().save(commit)
