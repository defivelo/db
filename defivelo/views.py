from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        # Add our menu_category context
        context['menu_category'] = 'home'
        return context
