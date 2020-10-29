from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import formset_factory
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from rolepermissions.checkers import has_role

from apps.challenge.models.session import Session
from apps.common.fields import CheckboxInput, NumberInput, TimeNumberInput
from apps.salary.models import (
    MonthlyCantonalValidation,
    MonthlyCantonalValidationUrl,
    Timesheet,
)

from . import BONUS_LEADER, HOURLY_RATE_HELPER, RATE_ACTOR


class TimesheetFormBase(forms.ModelForm):
    class Meta:
        model = Timesheet
        readonly = ("date", "time_helper", "actor_count", "leader_count", "ignore")
        fields = [
            "date",
            "time_helper",
            "actor_count",
            "leader_count",
            "overtime",
            "traveltime",
            "comments",
            "ignore",
        ]
        labels = {
            "time_helper": format_lazy(
                _("Heures moni·teur·trice ({price}.-/h)"), price=HOURLY_RATE_HELPER
            ),
            "actor_count": format_lazy(
                _("Intervention(s) ({price}.-/Qualif')"), price=RATE_ACTOR
            ),
            "leader_count": format_lazy(
                _("Participation(s) comme moni·teur·trice 2 ({price}.-/Qualif')"),
                price=BONUS_LEADER,
            ),
            "overtime": format_lazy(
                _("Heures supplémentaires ({price}.-/h)"), price=HOURLY_RATE_HELPER
            ),
            "traveltime": _("Heures de trajet (aller-retour)"),
            "ignore": _("Ne compter aucune heure de travail"),
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
                    "step": 1,
                    "min": 0,
                    "max": 2,
                    "class": "hide",
                    "data-unit-price": HOURLY_RATE_HELPER,
                }
            ),
            "ignore": CheckboxInput(
                attrs={
                    "data-function": "ignore",
                    "readonly": "readonly",
                    "disabled": "disabled",
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
                    "Vous ne pouvez pas rentrer des heures pour le %(day)s: aucune qualif ce jour-ci."
                ),
                params={"day": cleaned_data["date"]},
            )

        if cleaned_data["overtime"] != 0.0 and not cleaned_data["comments"]:
            self.add_error(
                "comments",
                forms.ValidationError(
                    _(
                        "Les remarques doivent être renseignées pour tout prétention d'heures supplémentaires"
                    )
                ),
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

        # Show restricted ignore checkboxes they were ticked by a StateManager.
        if self.initial.get("ignore"):
            self.fields["ignore"].widget.attrs["readonly"] = "readonly"
            self.fields["ignore"].widget.attrs["disabled"] = "disabled"
        else:
            self.fields["ignore"].widget = forms.HiddenInput()

    def clean(self):
        """
        Never allow ignore to be set through this one form
        """
        cleaned_data = super().clean()
        del cleaned_data["ignore"]
        return cleaned_data


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

        # StateManagers can fiddle with it
        del self.fields["ignore"].widget.attrs["readonly"]
        del self.fields["ignore"].widget.attrs["disabled"]

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

    def __init__(self, validator, urls, timesheets_statuses, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator
        self.timesheets_are_validated = timesheets_statuses[self.instance.canton]
        # Add the urls as checkboxes, but first; so:
        # Store away the fields
        fields = self.fields.copy()
        # Empty it
        self.fields = {}
        # Add our fake validations status
        self.fields["timesheets_checked"] = forms.BooleanField(
            label=_("Contrôle des heures effectué"),
            required=False,
            widget=CheckboxInput,
            help_text=mark_safe(
                '<a href="{url}" target="_blank">{text}</a>'.format(
                    url=reverse_lazy(
                        "salary:timesheets-overview",
                        kwargs={"year": self.instance.date.year},
                    ),
                    text=_("Contrôle des heures"),
                )
            ),
            initial=self.timesheets_are_validated,
            disabled=True,
        )
        # urls are MonthlyCantonalValidationUrl
        for url in urls:
            self.fields[f"url_{url.pk}"] = forms.BooleanField(
                label=url.name,
                required=False,
                widget=CheckboxInput,
                help_text=mark_safe(
                    f'<a href="{url.url}" target="_blank">{url.url}</a>'
                ),
                initial=self.instance.validated_urls.filter(pk=url.pk).exists(),
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
            # Verify that all URLs are ticked to allow validation
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
            if not self.timesheets_are_validated:
                self.add_error(
                    "timesheets_checked",
                    ValidationError(_("Les heures doivent être vérifiées")),
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
                try:
                    mcvu = MonthlyCantonalValidationUrl.objects.get(
                        pk=int(k.split("_")[1])
                    )
                    if self.cleaned_data[k]:
                        self.instance.validated_urls.add(mcvu)
                    else:
                        self.instance.validated_urls.remove(mcvu)
                except ValueError:  # Conversion of k.split("_")[1] to int; it's not an url
                    pass
        return super().save(commit)
