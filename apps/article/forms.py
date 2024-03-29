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
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.article.models import Article


class ArticleForm(forms.ModelForm):
    published = forms.BooleanField(label=_("Publié"), initial=True, required=False)

    def save(self, commit=True):
        instance = super(ArticleForm, self).save(commit=False)
        # Fix Deprecation Warning off simple-article
        instance.modified = timezone.now()
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Article
        fields = ["title", "body", "published"]
