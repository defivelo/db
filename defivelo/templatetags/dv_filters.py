from re import sub

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def setlang(request, newlang):
    """ Replace language code in request.path with the new language code
    """
    return sub('^/(%s)/' % request.LANGUAGE_CODE,
               '/%s/' % newlang, request.path)


@register.filter
def profile_tag(user):
    """
    Standard user display (currently fullname + small natel
    """
    if not user:
        return ''
    usertag = '<span>'
    usertag += user.get_full_name()
    if user.profile.natel:
        usertag += (
            '<br /><small><a href="tel:{natel}">{natel}</a></small>'
            .format(natel=user.profile.natel)
            )
    usertag += '</span>'

    return mark_safe(usertag)


@register.filter
def weeknumber(date):
    if not date:
        return ''
    # This "solves" the weird week numbers in templates
    return date.strftime('%W')
