# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2016 Didier Raboud <me+defivelo@odyx.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

from re import search, sub

from django import template
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from apps.challenge import (
    AVAILABILITY_FIELDKEY, AVAILABILITY_FIELDKEY_HELPER_PREFIX, SHORTCODE_ACTOR, SHORTCODE_MON1, SHORTCODE_MON2,
    SHORTCODE_SELECTED, STAFF_FIELDKEY, STAFF_FIELDKEY_HELPER_PREFIX,
)
from defivelo.roles import user_cantons

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
def tel_int(tel):
    if not tel:
        return ''
    # Delete spaces, drop initial 0, add +41
    return '+41' + tel.replace(' ', '')[1:]


@register.filter
def tel_link(tel):
    if not tel:
        return ''
    return mark_safe(
        '<a href="tel:{tel_int}">{tel}</a>'
        .format(tel_int=tel_int(tel), tel=tel)
        )


@register.filter
def profile_tag(user):
    """
    Standard user display (currently fullname + small natel)
    """
    if not user:
        return ''
    usertag = '<span>'
    usertag += user.get_full_name()
    if user.profile.natel:
        usertag += (
            '<br /><small>{tel_link}</small>'
            .format(tel_link=tel_link(user.profile.natel))
            )
    usertag += '</span>'

    return mark_safe(usertag)


@register.filter
def useravailsessions(form, user):
    """
    Output cells with form widget for all sessions concerning that user
    """
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
    """
    Output cells with the state of the availability / choice for all sessions,
    for that user
    """
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
                        if struct[staffkey] == SHORTCODE_MON2:
                            avail_verb = _('Moniteur 2')
                            avail_label = 'tags'
                        elif struct[staffkey] == SHORTCODE_MON1:
                            avail_verb = _('Moniteur 1')
                            avail_label = 'tag'
                        elif struct[staffkey] == SHORTCODE_ACTOR:
                            avail_verb = _('Intervenant')
                            avail_label = 'sunglasses'
                        elif struct[staffkey] == SHORTCODE_SELECTED:
                            avail_verb = _('Choisi')
                            avail_label = 'check'
                        else:
                            avail_verb = _('Pas choisi')
                            avail_label = 'unchecked'
            elif onlyavail:
                avail_content = ' '

            output += (
                '<td style="vertical-align: middle;"'
                '    class="{avail_class}"{avail_verbose}>'
                '<!-- {key} -->{avail_label}'
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
    """
    Output cells with the form widgets for session choice
    for that user
    """
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


@register.filter
def inusercantons(user, canton):
    try:
        usercantons = user_cantons(user)
        if usercantons:
            return canton in usercantons
        return True
    except PermissionDenied:
        return


@register.filter
def lettercounter(count):
    icount = int(count)
    if 0 <= icount <= 26:
        return chr(64 + icount)
    return icount
