from datetime import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse

from apps.challenge.forms.registration import (
    OrganizationSelectionForm,
    RegistrationConfirmForm,
    RegistrationFormSet,
)
from apps.challenge.models.registration import REGISTRATION_DAY_TIMES
from apps.orga.models import Organization


def register(request):
    if request.method == "POST":
        form = OrganizationSelectionForm(request.POST, user=request.user)
        formset = RegistrationFormSet(request.POST, form_kwargs={"user": request.user})
        if formset.is_valid() and form.is_valid():
            request.session["new_registration"] = {
                "organization": form.cleaned_data["organization"].id,
                "lines": formset.cleaned_data,
            }

            return HttpResponseRedirect(reverse("registration-confirm"))
    else:
        submitted = request.session.get("new_registration")
        initial = []
        if submitted:
            for line in submitted["lines"]:
                initial.append(
                    {
                        "date": datetime.fromisoformat(line["date"]),
                        "day_time": line["day_time"],
                        "classes_amount": line["classes_amount"],
                    }
                )

        form = OrganizationSelectionForm(user=request.user)
        formset = RegistrationFormSet(
            form_kwargs={"user": request.user}, initial=initial
        )

    return TemplateResponse(
        request=request,
        context={"form": form, "formset": formset},
        template="challenge/registration.html",
    )


def register_confirm(request):
    data = request.session["new_registration"]
    organization = get_object_or_404(Organization, pk=data["organization"])
    lines = []
    total_classes = 0
    for line in data["lines"]:
        lines.append(
            {
                "date": datetime.fromisoformat(line["date"]),
                "day_time": dict(REGISTRATION_DAY_TIMES)[line["day_time"]],
                "classes_amount": line["classes_amount"],
            }
        )
        total_classes += int(line["classes_amount"])

    if request.method == "POST":
        form = RegistrationConfirmForm(request.POST)
        if form.is_valid():
            # TODO
            #  - Create Registration instance
            #  - Send email to "Chargé de projet"
            #  - Redirect to ?
            pass
    else:
        form = RegistrationConfirmForm()

    return TemplateResponse(
        request=request,
        context={
            "organization": organization,
            "lines": lines,
            "total_classes": total_classes,
            "form": form,
        },
        template="challenge/registration_confirm.html",
    )
