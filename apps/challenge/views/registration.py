from django.template.response import TemplateResponse

from apps.challenge.forms.registration import RegistrationFormSet


def register(request):
    if request.method == 'POST':
        formset = RegistrationFormSet(request.POST, form_kwargs={'user': request.user})
        if formset.is_valid():
            # TODO Save registration with status pending
            #  Display confirmation page
            pass
    else:
        formset = RegistrationFormSet(form_kwargs={'user': request.user})

    return TemplateResponse(
        request=request,
        context={
            "formset": formset
        },
        template="challenge/registration.html"
    )
