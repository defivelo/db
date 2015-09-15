from datetime import date

from django.utils import timezone
from django.views.generic.base import TemplateView

from apps.challenge.models import Season


class MenuView(object):
    def get_context_data(self, **kwargs):
        context = super(MenuView, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['current_seasons'] = Season.objects.filter(end__gte=date.today())
        context['now'] = timezone.now()
        return context


class HomeView(MenuView, TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'home'
        return context
