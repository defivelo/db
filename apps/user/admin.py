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
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.db import transaction

from allauth.account.admin import EmailAddressAdmin as BaseEmailAddressAdmin
from allauth.account.models import EmailAddress

from .models import UserManagedState, UserProfile


class AdminUserProfile(admin.ModelAdmin):
    list_filter = ["updated_at"]


admin.site.register(UserProfile, AdminUserProfile)
admin.site.register(UserManagedState)


class UserChangeForm(BaseUserChangeForm):
    def clean_email(self):
        # allauth looks emails up lowercase, so store them that way
        return self.cleaned_data["email"].lower()


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)


class EmailAddressAdminForm(forms.ModelForm):
    class Meta:
        model = EmailAddress
        fields = "__all__"

    def _get_validation_exclusions(self):
        # unique_primary_email would reject a new primary before save() demotes
        # the previous one; the database still enforces it
        exclude = super()._get_validation_exclusions()
        exclude.add("primary")
        return exclude

    @transaction.atomic
    def save(self, commit=True):
        if self.cleaned_data["primary"] is True:
            EmailAddress.objects.filter(
                user=self.instance.user,
                primary=True,
            ).exclude(id=self.instance.id).update(primary=False)

        return super().save(commit)


class EmailAddressAdmin(BaseEmailAddressAdmin):
    list_filter = ("primary",)
    form = EmailAddressAdminForm


admin.site.unregister(EmailAddress)
admin.site.register(EmailAddress, EmailAddressAdmin)
