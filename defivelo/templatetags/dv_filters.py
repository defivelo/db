from re import sub

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def setlang(request, newlang):
    """ Replace language code in request.path with the new language code
    """
    return sub('^/(%s)/' % request.LANGUAGE_CODE,
               '/%s/' % newlang, request.path)
