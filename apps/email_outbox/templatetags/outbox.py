from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def is_supported_email_backend():
    return settings.EMAIL_BACKEND in (
        "django.core.mail.backends.locmem.EmailBackend",
        "django.core.mail.backends.filebased.EmailBackend",
    )
