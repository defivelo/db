from datetime import datetime

from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.challenge.forms.registration import (
    OrganizationSelectionForm,
    RegistrationConfirmForm,
    RegistrationFormSet,
    RegistrationValidationFormSet,
)
from apps.challenge.models.registration import REGISTRATION_DAY_TIMES, Registration
from apps.orga.models import Organization
from defivelo.roles import has_permission, user_cantons
from defivelo.templatetags.dv_filters import dv_season_url


def register(request):
    if not request.user.managed_organizations.exists():
        raise PermissionDenied

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
            formset = RegistrationFormSet(form_kwargs={"coordinator": request.user})
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
    if not request.user.managed_organizations.exists():
        raise PermissionDenied

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
            organization.notify_new_registrations(request)
            return redirect(reverse("home"))
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
    if not has_permission(request.user, "registration_validate"):
        raise PermissionDenied

    organizations = Organization.objects.filter(
        registration__isnull=False,
        registration__is_archived=False,
        address_canton__in=user_cantons(request.user),
    ).distinct()

    if request.method == "POST":
        organization = get_object_or_404(
            Organization, pk=request.POST.get("form-organization-id")
        )
        formset = RegistrationValidationFormSet(
            organization=organization,
            data=request.POST,
        )

        if formset.is_valid():
            formset.save()
            organization.notify_registrations_validated(request)
            return redirect(dv_season_url())

        else:
            data = []
            for other_organization in organizations:
                if organization == other_organization:
                    # This organization's formset has errors
                    data.append((organization, formset))
                else:
                    # These organizations' formsets haven't been submitted
                    data.append(
                        (
                            other_organization,
                            RegistrationValidationFormSet(
                                organization=other_organization,
                            ),
                        )
                    )
    else:
        data = [
            (
                organization,
                RegistrationValidationFormSet(
                    organization=organization,
                ),
            )
            for organization in organizations
        ]

    return TemplateResponse(
        request=request,
        context={"organizations": data},
        template="challenge/registration_validate.html",
    )
