from autocomplete_light import AutocompleteModelBase, register as al_register
from django.conf import settings
from django.contrib.auth import get_user_model


class UserAutocomplete(AutocompleteModelBase):
    search_fields = ['first_name', 'last_name']
    model = settings.AUTH_USER_MODEL

    def choice_label(self, choice):
        return "{name} ({level})".format(
            name=choice.get_full_name(),
            level=choice.profile.formation_full)

al_register(UserAutocomplete, name='Helpers',
            choices=get_user_model().objects.filter(
                profile__formation__in=['M1', 'M2']
                ),
            widget_attrs={
                'data-widget-maximum-values': 3,
            })
al_register(UserAutocomplete, name='Leaders',
            choices=get_user_model().objects.filter(profile__formation='M2'))
