from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from .forms import UserProfileForm
from .models import UserProfile


class UserDetail(DetailView):
    model = get_user_model()
    context_object_name = 'user'

    def get_object(self):
        """
        Only allow self-view for now
        """
        return get_user_model().objects.get(pk=self.request.user.pk)


class UserUpdate(SuccessMessageMixin, UpdateView):
    model = get_user_model()
    form_class = UserProfileForm
    template_name_suffix = '_update_form'
    success_message = _("Profil mis à jour")

    def get_object(self):
        """
        Only allow self-edits for now
        """
        return get_user_model().objects.get(pk=self.request.user.pk)

    def get_success_url(self):
        return reverse_lazy('user-update')

    def get_initial(self):
        """
        Pre-fill the form with the non-model fields
        """
        user = self.get_object()
        if hasattr(user, 'profile'):
            return {'iban': user.profile.iban}
        else:
            return {}

    def form_valid(self, form):
        """
        Write the non-model fields
        """
        if 'iban' in form.cleaned_data:
            (userprofile, created) = (
                UserProfile.objects.get_or_create(user=self.request.user)
            )
            userprofile.iban = form.cleaned_data['iban']
            userprofile.save()
        return super(UserUpdate, self).form_valid(form)
