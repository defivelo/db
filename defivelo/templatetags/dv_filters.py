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
from django.template.defaultfilters import date as datefilter
from django.utils.translation import get_language
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from memoize import memoize
from rolepermissions.templatetags.permission_tags import can_template_tag

from apps.challenge import (
    AVAILABILITY_FIELDKEY, AVAILABILITY_FIELDKEY_HELPER_PREFIX, CHOICE_FIELDKEY, CHOSEN_AS_ACTOR, CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER, CHOSEN_AS_LEGACY, CHOSEN_AS_NOT, CHOSEN_AS_REPLACEMENT, CONFLICT_FIELDKEY,
    SEASON_WORKWISH_FIELDKEY, STAFF_FIELDKEY, STAFF_FIELDKEY_HELPER_PREFIX,
)
from apps.common import (
    DV_SEASON_CHOICES, DV_STATE_CHOICES, DV_STATE_COLORS, DV_STATES_LONGER_ABBREVIATIONS, DV_STATES_REAL_FALLBACKS,
    STDGLYPHICON,
)
from apps.user import FORMATION_M1, FORMATION_M2, formation_short
from defivelo.roles import user_cantons

register = template.Library()


@memoize()
def can_memoized(user, role):
    return can_template_tag(user, role)


# Override 'can' from rolepermissions to add memoization for performance reasons
@register.filter
def can(user, role):
    return can_memoized(user, role)


@register.simple_tag
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
    return tel
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
        if (
            key == SEASON_WORKWISH_FIELDKEY.format(hpk=user.pk) or
            AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key
        ):
            output += '<td>{field}</td>'.format(
                field=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={'id': key})
                )
    return mark_safe(output)


@register.filter
def useravailsessions_readonly(struct, user, avail_forced_content=None, sesskey=None,
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
            avail_content = avail_forced_content
            conflict = False
            locked = False
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
                thissesskey = int(search(r'-s(\d+)', key).group(1))
                choicekey = CHOICE_FIELDKEY.format(hpk=user.pk,
                                                   spk=thissesskey)
                locked = choicekey in struct and struct[choicekey]

                conflictkey = CONFLICT_FIELDKEY.format(hpk=user.pk,
                                                       spk=thissesskey)
                conflicts = struct[conflictkey] if conflictkey in struct else []
                if len(conflicts) > 0:
                    conflict = conflicts.pop()

                # Si le choix des moniteurs est connu, remplace le label et
                # la version verbeuse par l'état du choix
                if not sesskey:
                    staffkey = STAFF_FIELDKEY.format(hpk=user.pk,
                                                     spk=thissesskey)
                    if staffkey in struct:
                        if struct[staffkey] == CHOSEN_AS_LEADER:
                            avail_verb = _('Moniteur 2')
                            avail_content = formation_short(FORMATION_M2)
                        elif struct[staffkey] == CHOSEN_AS_HELPER:
                            avail_verb = _('Moniteur 1')
                            avail_content = formation_short(FORMATION_M1)
                        elif struct[staffkey] == CHOSEN_AS_ACTOR:
                            avail_verb = _('Intervenant')
                            avail_label = 'sunglasses'
                        elif struct[staffkey] == CHOSEN_AS_REPLACEMENT:
                            avail_verb = _('Moniteur de secours')
                            avail_content = _('S')
                        elif struct[staffkey] == CHOSEN_AS_LEGACY:
                            avail_verb = _('Choisi')
                            avail_label = 'check'
                        else:
                            avail_verb = _('Pas choisi')
                            avail_label = 'unchecked'

            elif onlyavail:
                avail_content = ' '

            output += (
                '<td class="{avail_class}"{avail_verbose}>'
                '<!-- {key} -->{avail_label}{conflict_warning}'
                '</td>'
            ).format(
                avail_class='info' if locked else avail_class,
                avail_verbose=' title="%s"' % avail_verb if avail_verb else '',
                avail_label=(
                    avail_content if avail_content else
                    (STDGLYPHICON.format(
                        icon=avail_label,
                        title=avail_verb if avail_verb else ''
                    ) if avail_label else '')
                ),
                conflict_warning=(
                    (
                        '<a class="text-danger" href="{season_url}#sess{sessionpk}">{glyph}</a>'.format(
                            season_url=reverse(
                                'season-availabilities',
                                kwargs={'pk': conflict.session.season.pk}
                            ),
                            sessionpk=conflict.session.pk,
                            glyph=STDGLYPHICON.format(icon='alert', title=conflict.session)
                        )
                    ) if conflict else ''
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
                avail_forced_content=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={'id': key}))
    return mark_safe(output)


@register.filter
def chosen_staff_for_season(struct, user):
    if not struct or not user:
        return ''
    accu_in_qualif = 0
    accu_in_sess = 0
    for key in struct:
        if AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            if struct[key] in ['y', 'i']:
                thissesskey = int(search(r'-s(\d+)', key).group(1))
                choicekey = CHOICE_FIELDKEY.format(hpk=user.pk,
                                                   spk=thissesskey)
                if choicekey in struct and struct[choicekey]:
                    accu_in_qualif += 1

                staffkey = STAFF_FIELDKEY.format(hpk=user.pk,
                                                 spk=thissesskey)
                if staffkey in struct:
                    if struct[staffkey] != CHOSEN_AS_NOT:
                        accu_in_sess += 1
    #  if accu_in_qualif != accu_in_sess:
        #  return '%s/%s' % (accu_in_qualif, accu_in_sess)
    return accu_in_sess


@register.filter
def work_wish_for_season(struct, user):
    if not struct or not user:
        return ''
    workwishkey = SEASON_WORKWISH_FIELDKEY.format(hpk=user.pk)
    if workwishkey in struct:
        wish = int(struct[workwishkey])
        if wish > 0:
            return wish
    return ''


@register.filter
def weeknumber(date):
    if not date:
        return ''
    # This "solves" the weird week numbers in templates
    return date.strftime('%W')


@register.filter
def date_ch_short(date):
    if not date:
        return ''
    lang = get_language()
    if lang == 'de':
        return datefilter(date, 'j. N')
    else:
        return datefilter(date, 'j N')


@register.filter
def cantons_abbr(cantons, abbr=True, long=True, fix_special=False):
    special_cantons = DV_STATES_LONGER_ABBREVIATIONS if long else DV_STATES_REAL_FALLBACKS
    return [
                force_text(
                    c[1] if not fix_special
                    else special_cantons[c[0]] if c[0] in special_cantons else c[0]
                ) if not abbr
                else mark_safe(
                    '<abbr title="{title}">{abbr}</abbr>'
                    .format(
                        abbr=special_cantons[c[0]] if c[0] in special_cantons else c[0],
                        title=c[1]
                    )
                )
                for c in DV_STATE_CHOICES if c[0] in cantons
            ]


@register.filter
def canton_abbr(canton, abbr=True, long=True, fix_special=False):
    try:
        return cantons_abbr([canton], abbr, long, fix_special)[0]
    except IndexError:
        return ''


@register.filter
def canton_abbr_short(canton, abbr=True, fix_special=False):
    try:
        return cantons_abbr(
            [canton],
            abbr=abbr,
            long=False,
            fix_special=fix_special
        )[0]
    except IndexError:
        return ''


@register.filter
def ifcanton_abbr(canton):
    try:
        return canton_abbr(canton)
    except IndexError:
        return canton


@register.filter
def season_verb(season_id):
    try:
        return [s[1] for s in DV_SEASON_CHOICES if s[0] == season_id][0]
    except IndexError:
        return ''


@register.filter
def anyofusercantons(user, cantons):
    try:
        usercantons = user_cantons(user)
        return list(
            set(usercantons)
            .intersection(set(cantons))
        )
    except PermissionDenied:
        return


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


@register.simple_tag
def canton_colors():
    return DV_STATE_COLORS
