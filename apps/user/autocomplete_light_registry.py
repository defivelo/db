from autocomplete_light import AutocompleteModelBase, register as al_register
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.html import escape

from apps.challenge.models import MAX_MONO1_PER_QUALI


class UserAutocomplete(AutocompleteModelBase):
    search_fields = ['first_name', 'last_name']
    model = settings.AUTH_USER_MODEL

    def choice_html(self, choice):
        """
        Override autocomplete_light to drop the 'escape' call over choice_label
        """
        return self.choice_html_format % (
            escape(self.choice_value(choice)),
            self.choice_label(choice))

    def choice_label(self, choice):
        return "{name} {icon}".format(
            name=choice.get_full_name(),
            icon=choice.profile.formation_icon())

al_register(UserAutocomplete, name='Helpers',
            choices=get_user_model().objects.filter(
                profile__formation__in=['M1', 'M2']
                ),
            widget_attrs={
                'data-widget-maximum-values': MAX_MONO1_PER_QUALI,
            })
al_register(UserAutocomplete, name='Leaders',
            choices=get_user_model().objects.filter(profile__formation='M2'))
