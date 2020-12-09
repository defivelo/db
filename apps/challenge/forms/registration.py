from django import forms
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models.registration import Registration
from apps.common.forms import SwissDateField


class OrganizationSelectionForm(forms.Form):
    def __init__(self, *args, coordinator, **kwargs):
        super().__init__(*args, **kwargs)
        organizations = coordinator.managed_organizations.all()
        self.fields["organization"] = forms.ModelChoiceField(
            widget=forms.Select,
            queryset=organizations,
            required=True,
            initial=organizations.first(),
            label=_("Établissement"),
        )


class RegistrationForm(forms.ModelForm):
    date = SwissDateField(required=True)

    def __init__(self, *args, **kwargs):
        coordinator = kwargs.pop("coordinator", None)
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        self.instance.coordinator = coordinator
        self.instance.organization = organization
        self.fields["classes_amount"].widget.attrs["min"] = 1
        self.fields["classes_amount"].widget.attrs["max"] = 6

    class Meta:
        model = Registration
        fields = ("date", "day_time", "classes_amount")


class BaseRegistrationFormSet(forms.BaseFormSet):
    def serialize(self):
        return [
            {
                "date": form["date"].isoformat(),
                "day_time": form["day_time"],
                "classes_amount": form["classes_amount"],
            }
            for form in self.cleaned_data
        ]


RegistrationFormSet = formset_factory(
    RegistrationForm,
    formset=BaseRegistrationFormSet,
    extra=1,
    max_num=1,
    min_num=1,
    validate_min=True,
)


class RegistrationConfirmForm(forms.Form):
    is_terms_accepted = forms.BooleanField(
        label=_("J'accepte les conditions générales"),
        required=True,
        initial=False,
    )
