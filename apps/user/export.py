# -*- coding: utf-8 -*-
#
# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015 Didier Raboud <me+defivelo@odyx.org>
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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from import_export import fields, resources, widgets

from .models import STD_PROFILE_FIELDS


class MultipleSelectWidget(widgets.Widget):
    def render(self, value):
        return ', '.join(value)


class FirstMedWidget(widgets.Widget):
    def render(self, object):
        final = _('Yes') if object.firstmed_course else _('No')
        if object.firstmed_course_comm:
            final += ' - ' + object.firstmed_course_comm
        return force_text(final)


class ObjectMethodWidget(widgets.Widget):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        return super(ObjectMethodWidget, self).__init__(*args, **kwargs)

    def render(self, object):
        attribute = getattr(object, self.method)
        if attribute:
            return force_text(attribute)
        return ''

ALL_PROFILE_FIELDS = tuple(
    ['first_name', 'last_name', 'email'] +
    ['profile__%s' % field for field in STD_PROFILE_FIELDS
     if field not in ['firstmed_course_comm']]
)


class UserResource(resources.ModelResource):
    first_name = fields.Field(column_name=_('Prénom'), attribute='first_name')
    last_name = fields.Field(column_name=_('Nom'), attribute='last_name')
    email = fields.Field(column_name=_('Email'), attribute='email')
    profile__natel = fields.Field(column_name=_('Natel'),
                                  attribute='profile__natel')
    profile__address_street = fields.Field(column_name=_('Rue'),
                                           attribute='profile__address_street')
    profile__address_no = fields.Field(column_name=_('N°'),
                                       attribute='profile__address_no')
    profile__address_zip = fields.Field(column_name=_('NPA'),
                                        attribute='profile__address_zip')
    profile__address_city = fields.Field(column_name=_('Ville'),
                                         attribute='profile__address_city')
    profile__address_canton = fields.Field(column_name=_('Canton'),
                                           attribute='profile__address_canton')
    profile__birthdate = fields.Field(
        column_name=_('Date de naissance'), attribute='profile__birthdate',
        widget=widgets.DateWidget(format='%d.%m.%Y')
    )
    profile__social_security = fields.Field(
        column_name=_('N° AVS'), attribute='profile__social_security')
    profile__pedagogical_experience = fields.Field(
        column_name=_('Expérience pédagogique'),
        attribute='profile__pedagogical_experience')
    profile__comments = fields.Field(
        column_name=_('Commentaires'),
        attribute='profile__comments')
    # From there, specific widgets
    profile__firstmed_course = fields.Field(
        column_name=_('Cours samaritains'),
        attribute='profile',
        widget=FirstMedWidget())
    profile__actor_for = fields.Field(
        column_name=_("Intervenant"),
        attribute='profile',
        widget=ObjectMethodWidget(method='actor_for'))
    profile__status = fields.Field(
        column_name=_("Statut"),
        attribute='profile',
        widget=ObjectMethodWidget(method='status_full'))
    profile__bagstatus = fields.Field(
        column_name=_('Sac Défi Vélo'),
        attribute='profile',
        widget=ObjectMethodWidget(method='bagstatus_full'))
    profile__formation = fields.Field(
        column_name=_("Formation"),
        attribute='profile',
        widget=ObjectMethodWidget(method='formation_full'))
    profile__affiliation_canton = fields.Field(
        column_name=_("Canton d'affiliation"),
        attribute='profile__affiliation_canton')
    profile__iban = fields.Field(
        column_name=_("IBAN"),
        attribute='profile',
        widget=ObjectMethodWidget(method='iban_nice'))
    profile__office_member = fields.Field(
        column_name=_('Bureau Défi Vélo'),
        attribute='profile__office_member')

    class Meta:
        model = get_user_model()
        fields = ALL_PROFILE_FIELDS
        export_order = ALL_PROFILE_FIELDS
