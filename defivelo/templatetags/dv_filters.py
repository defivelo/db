# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import sub

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

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
def useravailsessions(form, user):
    if not form or not user:
        return ''
    output = ''
    for key in form.fields:
        if 'avail-h{hpk}'.format(hpk=user.pk) in key:
            output += '<td>{field}</td>'.format(
                field=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={'id': key})
                )
    return mark_safe(output)


@register.filter
def useravailsessions_readonly(struct, user):
    if not struct or not user:
        return ''
    output = ''
    for key in struct:
        if 'avail-h{hpk}'.format(hpk=user.pk) in key:
            availability = struct[key]
            avail_verb = ''  # Fulltext
            avail_label = ''  # Bootstrap glyphicon name
            avail_class = 'active'  # Bootstrap array cell class
            if availability == 'i':
                # If needed
                avail_verb = _('Si nécessaire')
                avail_label = 'ok-circle'
                avail_class = 'warning'
            elif availability == 'n':
                avail_verb = _('Non')
                avail_label = 'remove-sign'
                avail_class = 'danger'
            elif availability == 'y':
                avail_verb = _('Oui')
                avail_label = 'ok-sign'
                avail_class = 'success'
            output += (
                '<td class="{avail_class}"{avail_verbose}>{avail_label}'
                '</td>'
            ).format(
                avail_class=avail_class,
                avail_verbose=' title="%s"' % avail_verb if avail_verb else '',
                avail_label=(
                    '<span class="glyphicon glyphicon-%s"></span> '
                    % avail_label
                    if avail_label else ''
                    )
            )
    return mark_safe(output)


@register.filter
def weeknumber(date):
    if not date:
        return ''
    # This "solves" the weird week numbers in templates
    return date.strftime('%W')
