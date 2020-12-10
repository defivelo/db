from datetime import datetime

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from apps.challenge.forms.registration import (
    OrganizationSelectionForm,
    RegistrationConfirmForm,
    RegistrationFormSet,
    RegistrationValidationFormSet,
)
from apps.challenge.models.registration import REGISTRATION_DAY_TIMES, Registration
from apps.orga.models import Organization


def register(request):
    # TODO Limit with permissions to coordinator or stronger
    if request.method == "POST":
        organization_form = OrganizationSelectionForm(
            request.POST, coordinator=request.user
        )
        if organization_form.is_valid():
            formset = RegistrationFormSet(
                request.POST,
                form_kwargs={
                    "coordinator": request.user,
                    "organization": organization_form.cleaned_data["organization"],
                },
            )

            if formset.is_valid():
                request.session["new_registration"] = {
                    "organization": organization_form.cleaned_data["organization"].id,
                    "lines": formset.serialize(),
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

        organization_form = OrganizationSelectionForm(coordinator=request.user)
        formset = RegistrationFormSet(
            form_kwargs={"coordinator": request.user}, initial=initial
        )

    return TemplateResponse(
        request=request,
        context={"form": organization_form, "formset": formset},
        template="challenge/registration.html",
    )


def register_confirm(request):
    # TODO Limit with permissions to coordinator or stronger
    data = request.session.get("new_registration")
    if not data:
        raise SuspiciousOperation(_("Aucune inscription à valider"))

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
            for line in data["lines"]:
                Registration.objects.create(
                    date=datetime.fromisoformat(line["date"]),
                    day_time=line["day_time"],
                    classes_amount=line["classes_amount"],
                    coordinator=request.user,
                    organization=organization,
                )
            del request.session["new_registration"]
            # TODO
            #  - Send email to "Chargé de projet"
            #  - Redirect to ?
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


def register_validate(request):
    # TODO Limit with permissions to chargé-de-projet or stronger
    registrations = Registration.objects.all()

    return TemplateResponse(
        request=request,
        context={
            "formset": RegistrationValidationFormSet()
        },
        template="challenge/registration_validate.html",
    )
