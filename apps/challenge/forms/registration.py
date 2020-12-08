from django import forms
from django.forms import formset_factory

from apps.challenge.models.registration import Registration
from apps.common.forms import SwissDateField


class RegistrationForm(forms.ModelForm):
    date = SwissDateField()

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    class Meta:
        model = Registration
        fields = ("date", "day_time", "classes_amount")


RegistrationFormSet = formset_factory(
    RegistrationForm,
    extra=1
)
