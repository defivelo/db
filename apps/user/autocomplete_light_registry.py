from autocomplete_light import AutocompleteModelBase, register as al_register
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.html import escape

from apps.challenge import MAX_MONO1_PER_QUALI


class PersonAutocomplete(AutocompleteModelBase):
    search_fields = ['first_name', 'last_name']
    model = settings.AUTH_USER_MODEL

    def choice_label(self, choice):
        return choice.get_full_name()

    def choice_html(self, choice):
        """
        Override autocomplete_light to drop the 'escape' call over choice_label
        """
        return self.choice_html_format % (
            escape(self.choice_value(choice)),
            self.choice_label(choice))

al_register(PersonAutocomplete, name='AllPersons',
            choices=get_user_model().objects.all(),
            widget_attrs={
                'data-widget-maximum-values': 1,
            })

al_register(PersonAutocomplete, name='PersonsRelevantForSessions',
            choices=get_user_model().objects.filter(
                Q(profile__formation__in=['M1', 'M2']) | Q(profile__actor_for__isnull=False)
            ),
            widget_attrs={
                'data-widget-maximum-values': 1,
            })

class HelpersAutocomplete(PersonAutocomplete):
    def choice_label(self, choice):
        return "{name} {icon}".format(
            name=choice.get_full_name(),
            icon=choice.profile.formation_icon())

al_register(HelpersAutocomplete, name='Helpers',
            choices=get_user_model().objects.filter(
                profile__formation__in=['M1', 'M2']
                ),
            widget_attrs={
                'data-widget-maximum-values': MAX_MONO1_PER_QUALI,
            })
al_register(HelpersAutocomplete, name='Leaders',
            choices=get_user_model().objects.filter(profile__formation='M2'))


class ActorsAutocomplete(PersonAutocomplete):
    def choice_label(self, choice):
        return "{name} ({actor_for})".format(
            name=choice.get_full_name(),
            actor_for=choice.profile.actor_for.name)


al_register(ActorsAutocomplete, name='Actors',
            choices=get_user_model().objects.exclude(profile__actor_for__isnull=True))
