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

from article.models import Article
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView

from defivelo.views import MenuView

from .forms import ArticleForm


class ArticleMixin(MenuView):
    model = Article
    context_object_name = 'article'
    form_class = ArticleForm
    success_url = reverse_lazy('home')


class ArticleCreateView(ArticleMixin,
                        SuccessMessageMixin,
                        CreateView):
    success_message = _("Article créé")
    
class ArticleUpdateView(ArticleMixin,
                        SuccessMessageMixin,
                        UpdateView):
    success_message = _("Article mis à jour")
