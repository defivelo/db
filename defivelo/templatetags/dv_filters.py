# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import search, sub

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.challenge import (
    AVAILABILITY_FIELDKEY, AVAILABILITY_FIELDKEY_HELPER_PREFIX, STAFF_FIELDKEY,
    STAFF_FIELDKEY_HELPER_PREFIX,
)

register = template.Library()


@register.assignment_tag
def vcs_version():
    return settings.VCS_VERSION


@register.simple_tag
def vcs_commit():
    return settings.VCS_COMMIT


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
        if AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            output += '<td>{field}</td>'.format(
                field=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={'id': key})
                )
    return mark_safe(output)


@register.filter
def useravailsessions_readonly(struct, user, avail_content=None, sesskey=None,
                               onlyavail=False):
    if not struct or not user:
        return ''
    output = ''
    for key in struct:
        if AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            # If there's a sessionkey specified, skip the ones not
            # corresponding
            if sesskey:
                if key != AVAILABILITY_FIELDKEY.format(hpk=user.pk,
                                                       spk=sesskey):
                    continue
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

            if availability in ['y', 'i']:
                # Si le choix des moniteurs est connu, remplace le label et
                # la version verbeuse par l'état du choix
                if not sesskey:
                    thissesskey = int(search(r'-s(\d+)', key).group(1))
                    staffkey = STAFF_FIELDKEY.format(hpk=user.pk,
                                                     spk=thissesskey)
                    if staffkey in struct:
                        if struct[staffkey]:
                            avail_label = 'check'
                            avail_verb = _('Choisi')
                        else:
                            avail_label = 'unchecked'
                            avail_verb = _('Pas choisi')
            elif onlyavail:
                avail_content = ' '

            output += (
                '<td class="{avail_class}"{avail_verbose}>'
                '<!-- {key} -->'
                '{avail_label}'
                '</td>'
            ).format(
                avail_class=avail_class,
                avail_verbose=' title="%s"' % avail_verb if avail_verb else '',
                avail_label=(
                    avail_content if avail_content else
                    ('<span class="glyphicon glyphicon-%s"></span> '
                        % avail_label
                        if avail_label else '')
                    ),
                key=key,
            )
    return mark_safe(output)



@register.filter
def userstaffsessions(form, user):
    if not form or not user:
        return ''
    output = ''
    for key in form.fields:
        if STAFF_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            # Lookout for the session key in the form field key, and pipe
            # it to the useravailsessions_readonly function
            sesskey = int(search(r'-s(\d+)', key).group(1))
            output += useravailsessions_readonly(
                struct=form.initial,
                user=user,
                sesskey=sesskey,
                onlyavail=True,
                avail_content=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={'id': key}))
    return mark_safe(output)


@register.filter
def chosen_staff_for_season(user, season):
    return user.availabilities.filter(
        availability__in=['i', 'y'],
        chosen=True,
        session__in=season.sessions).count()


@register.filter
def weeknumber(date):
    if not date:
        return ''
    # This "solves" the weird week numbers in templates
    return date.strftime('%W')
