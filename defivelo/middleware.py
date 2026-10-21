from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allauth.mfa.models import Authenticator
from allauth.mfa.utils import is_mfa_enabled
from rolepermissions.checkers import has_role

REQUIRED_MFA_TYPES = [Authenticator.Type.TOTP, Authenticator.Type.WEBAUTHN]
EXEMPT_PATH_PREFIXES = ("/accounts/", "/static/", "/media/", "/i18n/")


def user_requires_mfa(user) -> bool:
    return user.is_superuser or has_role(user, "power_user")


class RequireMFAMiddleware:
    """
    Forces PowerUsers and superusers to have a TOTP or WebAuthn
    authenticator configured before they can use the rest of the app.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            settings.MFA_ENFORCEMENT_ENABLED
            and user is not None
            and user.is_authenticated
            and not request.path.startswith(EXEMPT_PATH_PREFIXES)
            and user_requires_mfa(user)
            and not is_mfa_enabled(user, REQUIRED_MFA_TYPES)
        ):
            messages.warning(
                request,
                _(
                    "Votre rôle nécessite l'activation de l'authentification "
                    "à deux facteurs pour continuer."
                ),
            )
            return redirect(reverse("mfa_index"))
        return self.get_response(request)
