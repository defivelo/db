from django import forms
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from apps.challenge.models.registration import Registration
from apps.common.forms import SwissDateField


class OrganizationSelectionForm(forms.Form):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        organizations = user.managed_organizations.all()
        self.fields["organization"] = forms.ModelChoiceField(
            widget=forms.Select,
            queryset=organizations,
            required=True,
            initial=organizations.first(),
            label=_("Établissement"),
        )


class RegistrationForm(forms.ModelForm):
    date = SwissDateField()

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["classes_amount"].widget.attrs["min"] = 1
        self.fields["classes_amount"].widget.attrs["max"] = 6

    class Meta:
        model = Registration
        fields = ("date", "day_time", "classes_amount")

    def clean_date(self):
        return self.cleaned_data["date"].isoformat()


RegistrationFormSet = formset_factory(RegistrationForm, extra=1, max_num=1)


class RegistrationConfirmForm(forms.Form):
    is_terms_accepted = forms.BooleanField(
        label=_("J'accepte les conditions générales"),
        required=True,
        initial=False,
    )
