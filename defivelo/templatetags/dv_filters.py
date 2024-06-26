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

import datetime
import urllib.parse
from re import search, sub

from django import template
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.template.defaultfilters import date as datefilter
from django.urls import reverse
from django.utils.dates import MONTHS
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from memoize import memoize
from rolepermissions.templatetags.permission_tags import can_template_tag

from apps.challenge import (
    AVAILABILITY_FIELDKEY,
    AVAILABILITY_FIELDKEY_HELPER_PREFIX,
    CHOICE_FIELDKEY,
    CHOSEN_AS_ACTOR,
    CHOSEN_AS_HELPER,
    CHOSEN_AS_LEADER,
    CHOSEN_AS_LEGACY,
    CHOSEN_AS_NOT,
    CHOSEN_AS_REPLACEMENT,
    CONFLICT_FIELDKEY,
    SEASON_WORKWISH_FIELDKEY,
    STAFF_FIELDKEY,
    STAFF_FIELDKEY_HELPER_PREFIX,
    SUPERLEADER_FIELDKEY,
)
from apps.common import (
    DV_SEASON_AUTUMN,
    DV_SEASON_CHOICES,
    DV_SEASON_LAST_SPRING_MONTH,
    DV_SEASON_SPRING,
    DV_STATE_CHOICES,
    DV_STATE_COLORS,
    STDGLYPHICON,
)
from apps.user import FORMATION_M1, FORMATION_M2, formation_short
from defivelo.roles import has_permission, user_cantons

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
    """Replace language code in request.path with the new language code"""
    return sub("^/(%s)/" % request.LANGUAGE_CODE, "/%s/" % newlang, request.path)


@register.filter
def tel_int(tel):
    if not tel:
        return ""
    # Delete spaces, drop initial 0, add +41
    return "+41" + tel.replace(" ", "")[1:]


@register.filter
def tel_link(tel):
    if not tel:
        return ""
    if tel[0:3] == "+41" and len(tel) == 12:
        # Convert to swiss local number
        tel_str = "0{} {} {} {}".format(tel[3:5], tel[5:8], tel[8:10], tel[10:12])
    else:
        tel_str = tel
    return mark_safe(
        '<a href="tel:{tel_int}">{tel}</a>'.format(tel_int=tel_int(tel), tel=tel_str)
    )


@register.filter
def profile_tag(user, is_restricted: bool = False):
    """
    Standard user display (currently fullname + small natel)
    """
    if not user:
        return ""
    usertag = "<span>"
    usertag += user.get_full_name()
    if user.profile.natel and not is_restricted:
        usertag += "<br /><small>{tel_link}</small>".format(
            tel_link=tel_link(user.profile.natel)
        )
    usertag += "</span>"

    return mark_safe(usertag)


@register.filter
def useravailsessions(form, user):
    """
    Output cells with form widget for all sessions concerning that user
    """
    if not form or not user:
        return ""
    output = ""
    for key in form.fields:
        if (
            key == SEASON_WORKWISH_FIELDKEY.format(hpk=user.pk)
            or AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key
        ):
            output += "<td>{field}</td>".format(
                field=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={"id": key}
                )
            )
    return mark_safe(output)


@register.filter
def useravailsessions_readonly(
    struct,
    user,
    avail_forced_content=None,
    sesskey=None,
    onlyavail=False,
    planning=False,
):
    """
    Output cells with the state of the availability / choice for all sessions,
    for that user
    """
    if not struct or not user:
        return ""
    output = ""
    for key in struct:
        if AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            # If there's a sessionkey specified, skip the ones not
            # corresponding
            if sesskey:
                if key != AVAILABILITY_FIELDKEY.format(hpk=user.pk, spk=sesskey):
                    continue
            availability = struct[key]
            avail_verb = ""  # Fulltext
            avail_label = ""  # Bootstrap glyphicon name
            avail_class = "active"  # Bootstrap array cell class
            avail_content = avail_forced_content
            conflict = False
            locked = False
            superleader = False
            if not planning:
                if availability == "i":
                    # If needed
                    avail_verb = _("Si nécessaire")
                    avail_label = "ok-circle"
                    avail_class = "warning"
                elif availability == "n":
                    avail_verb = _("Non")
                    avail_label = "remove-sign"
                    avail_class = "danger"
                elif availability == "y":
                    avail_verb = _("Oui")
                    avail_label = "ok-sign"
                    avail_class = "success"

            thissesskey = int(search(r"-s(\d+)", key).group(1))

            slkey = SUPERLEADER_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
            superleader = slkey in struct and struct[slkey]

            if availability in ["y", "i"]:
                choicekey = CHOICE_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
                locked = choicekey in struct and struct[choicekey]

                conflictkey = CONFLICT_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
                conflicts = struct[conflictkey] if conflictkey in struct else []
                if len(conflicts) > 0:
                    conflict = conflicts.pop()

                # Si le choix des moniteurs est connu, remplace le label et
                # la version verbeuse par l’état du choix
                if not sesskey:
                    staffkey = STAFF_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
                    if staffkey in struct:
                        if struct[staffkey] == CHOSEN_AS_LEADER:
                            avail_verb = _("Moniteur 2")
                            avail_content = formation_short(FORMATION_M2)
                        elif struct[staffkey] == CHOSEN_AS_HELPER:
                            avail_verb = _("Moniteur 1")
                            avail_content = formation_short(FORMATION_M1)
                        elif struct[staffkey] == CHOSEN_AS_ACTOR:
                            avail_verb = _("Intervenant")
                            avail_label = "sunglasses"
                        elif struct[staffkey] == CHOSEN_AS_REPLACEMENT:
                            avail_verb = _("Moniteur de secours")
                            avail_content = _("S")
                        elif struct[staffkey] == CHOSEN_AS_LEGACY:
                            avail_verb = _("Choisi")
                            avail_label = "check"
                        else:
                            if not planning:
                                avail_verb = _("Pas choisi")
                                avail_label = "unchecked"

            elif onlyavail:
                avail_content = " "

            final_avail_label = (
                avail_content
                if avail_content
                else (
                    STDGLYPHICON.format(
                        icon=avail_label, title=avail_verb if avail_verb else ""
                    )
                    if avail_label
                    else ""
                )
            )

            output += (
                '<td class="{avail_class}"{avail_verbose}><div class="dvflex">'
                "<!-- {key} -->{avail_label}{superleader}{conflict_warning}"
                "</div></td>"
            ).format(
                avail_class="info" if locked else avail_class,
                avail_verbose=' title="%s"' % avail_verb if avail_verb else "",
                avail_label=final_avail_label,
                superleader=(
                    ("&nbsp;/&nbsp;" if final_avail_label else "")
                    + '<span title="{mplus}">{mplus_short}</span>'.format(
                        mplus=_("Moniteur + / Photographe"), mplus_short=_("M+")
                    )
                )
                if superleader and planning
                else "",
                conflict_warning=(
                    (
                        '<a class="text-danger" href="{season_url}#sess{sessionpk}">{glyph}</a>'.format(
                            season_url=reverse(
                                "season-availabilities",
                                kwargs={"pk": conflict.session.season.pk},
                            ),
                            sessionpk=conflict.session.pk,
                            glyph=STDGLYPHICON.format(
                                icon="alert", title=conflict.session
                            ),
                        )
                    )
                    if conflict and not planning
                    else ""
                ),
                key=key,
            )
    return mark_safe(output)


@register.filter
def userplanning_sessions_readonly(struct, user):
    """
    Output cells with the state of the availability / choice for all sessions,
    for that user
    """
    return useravailsessions_readonly(struct, user, planning=True)


@register.filter
def userstaffsessions(form, user):
    """
    Output cells with the form widgets for session choice
    for that user
    """
    if not form or not user:
        return ""
    output = ""
    for key in form.fields:
        if STAFF_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            # Lookout for the session key in the form field key, and pipe
            # it to the useravailsessions_readonly function
            sesskey = int(search(r"-s(\d+)", key).group(1))
            output += useravailsessions_readonly(
                struct=form.initial,
                user=user,
                sesskey=sesskey,
                onlyavail=True,
                avail_forced_content=form.fields[key].widget.render(
                    key, form.fields[key].initial, attrs={"id": key}
                ),
            )
    return mark_safe(output)


@register.filter
def chosen_staff_for_season(struct, user):
    if not struct or not user:
        return ""
    accu_in_qualif = 0
    accu_in_sess = 0
    for key in struct:
        if AVAILABILITY_FIELDKEY_HELPER_PREFIX.format(hpk=user.pk) in key:
            if struct[key] in ["y", "i"]:
                thissesskey = int(search(r"-s(\d+)", key).group(1))
                choicekey = CHOICE_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
                if choicekey in struct and struct[choicekey]:
                    accu_in_qualif += 1

                staffkey = STAFF_FIELDKEY.format(hpk=user.pk, spk=thissesskey)
                if staffkey in struct:
                    if struct[staffkey] != CHOSEN_AS_NOT:
                        accu_in_sess += 1
    #  if accu_in_qualif != accu_in_sess:
    #  return '%s/%s' % (accu_in_qualif, accu_in_sess)
    return accu_in_sess


@register.filter
def work_wish_for_season(struct, user):
    if not struct or not user:
        return ""
    workwishkey = SEASON_WORKWISH_FIELDKEY.format(hpk=user.pk)
    if workwishkey in struct:
        wish = int(struct[workwishkey])
        if wish > 0:
            return wish
    return ""


@register.filter
def weeknumber(date):
    if not date:
        return ""
    # This "solves" the weird week numbers in templates
    return date.strftime("%W")


@register.filter
def date_ch_short(date):
    if not date:
        return ""
    lang = get_language()
    if lang == "de":
        return datefilter(date, "j. N")
    else:
        return datefilter(date, "j N")


@register.filter
def cantons_abbr(cantons, abbr=True, long=True):
    return [
        force_str(c[1])
        if not abbr
        else mark_safe(
            '<abbr title="{title}">{abbr}</abbr>'.format(
                abbr=c[0],
                title=c[1],
            )
        )
        for c in DV_STATE_CHOICES
        if c[0] in cantons
    ]


@register.filter
def canton_abbr(canton, abbr=True, long=True):
    try:
        return cantons_abbr([canton], abbr, long)[0]
    except IndexError:
        return canton


@register.filter
def canton_abbr_short(canton, abbr=True):
    try:
        return cantons_abbr([canton], abbr=abbr, long=False)[0]
    except IndexError:
        return canton


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
        return ""


@register.simple_tag
def dv_season(day=None):
    """
    Structure (kwargs) for the current (or specified) DV season
    """
    if not day:
        day = datetime.datetime.today()
    return {
        "year": day.year,
        "dv_season": (
            DV_SEASON_SPRING
            if day.month <= DV_SEASON_LAST_SPRING_MONTH
            else DV_SEASON_AUTUMN
        ),
    }


@register.simple_tag
def dv_season_url(day=None):
    """
    URL of the current (or specified) DV season list view
    """
    return reverse("season-list", kwargs=dv_season(day))


@register.filter
def season_month_start(season_id):
    for s in DV_SEASON_CHOICES:
        if s[0] == season_id:
            try:
                return MONTHS[
                    1
                    + (
                        0
                        if season_id == DV_SEASON_SPRING
                        else DV_SEASON_LAST_SPRING_MONTH
                    )
                ]
            except IndexError:
                pass
    return ""


@register.filter
def season_month_end(season_id):
    for s in DV_SEASON_CHOICES:
        if s[0] == season_id:
            try:
                return MONTHS[
                    (
                        DV_SEASON_LAST_SPRING_MONTH
                        if season_id == DV_SEASON_SPRING
                        else 12
                    )
                ]
            except IndexError:
                pass
    return ""


@register.filter
def anyofusercantons(user, cantons):
    try:
        usercantons = user_cantons(user)
        return list(set(usercantons).intersection(set(cantons)))
    except PermissionDenied:
        return


@register.filter
def unprivileged_user_can_see(user, season):
    return season.unprivileged_user_can_see(user)


@register.filter
def inusercantons(user, canton):
    if has_permission(user, "cantons_all"):
        # Also True for `canton == ''`
        return True
    try:
        usercantons = user_cantons(user)
    except LookupError:
        return False
    else:
        return canton in usercantons


@register.filter
def lettercounter(count):
    icount = int(count)
    if 0 <= icount <= 26:
        return chr(64 + icount)
    return icount


@register.simple_tag
def canton_colors():
    return DV_STATE_COLORS


@register.filter
def remove_qs(url, param_name):
    """
    Remove all occurences of the querystring named `param_name` from the given URL.
    """
    parsed_url = urllib.parse.urlparse(url)
    parsed_qs = urllib.parse.parse_qsl(parsed_url.params)
    qs_without_param = [
        (name, value) for name, value in parsed_qs if name != param_name
    ]
    encoded_qs_without_param = urllib.parse.urlencode(qs_without_param)

    return urllib.parse.urlunparse(parsed_url._replace(query=encoded_qs_without_param))


@register.simple_tag
def add_qs(url, **kwargs):
    """
    Add all kwargs and their values as querystrings to the given URL.
    """
    parsed_url = urllib.parse.urlparse(url)
    new_qs = urllib.parse.parse_qsl(parsed_url.params) + [
        (name, value) for name, value in kwargs.items()
    ]
    new_qs_encoded = urllib.parse.urlencode(new_qs)

    return urllib.parse.urlunparse(parsed_url._replace(query=new_qs_encoded))


@register.filter
def get_timesheet_status_for_canton(mcv, timesheets_status):
    """
    mcv is the object
    timesheets_status is the canton's array of timesheet statuses
    """
    return timesheets_status.get(mcv.canton, None)
