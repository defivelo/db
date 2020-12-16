from django import forms
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models import Qualification, Session
from apps.challenge.models.registration import Registration
from apps.common.forms import SwissDateField
from defivelo.templatetags.dv_filters import lettercounter


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
    date = SwissDateField()

    def __init__(self, *args, **kwargs):
        coordinator = kwargs.pop("coordinator")
        organization = kwargs.pop("organization")
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


RegistrationFormSet = forms.formset_factory(
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


class RegistrationValidationForm(forms.ModelForm):
    date = SwissDateField()
    is_validated = forms.BooleanField(
        initial=False, widget=forms.HiddenInput, required=False
    )

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        self.instance.organization = organization
        self.instance.coordinator = organization.coordinator

        self.fields["day_time"].widget.attrs["disabled"] = True
        self.fields["date"].widget.attrs["readonly"] = True
        self.fields["classes_amount"].widget.attrs["readonly"] = True

    def save(self, commit=True):
        instance = super().save(commit=commit)

        if self.cleaned_data["is_validated"]:
            session = Session.objects.create(
                day=instance.date,
                orga=instance.organization,
                begin=instance.day_time,
            )
            for i in range(instance.classes_amount):
                Qualification.objects.create(
                    session=session, name=_("Classe %s") % lettercounter(i + 1)
                )
            instance.archive()

    class Meta:
        model = Registration
        fields = ("id", "date", "day_time", "classes_amount")


class BaseRegistrationValidationFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization")
        super().__init__(
            *args,
            queryset=Registration.objects.filter(
                organization=organization, is_archived=False
            ),
            form_kwargs={"organization": organization},
            **kwargs,
        )


RegistrationValidationFormSet = forms.modelformset_factory(
    Registration,
    form=RegistrationValidationForm,
    formset=BaseRegistrationValidationFormSet,
    extra=0,
    can_delete=True,
)
