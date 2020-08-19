# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2016 Didier Raboud <me+defivelo@odyx.org>
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

from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from import_export.formats import base_formats


class ExportMixin(object):
    export_class = None
    export_filename = None

    def render_to_response(self, context, **response_kwargs):
        resolvermatch = self.request.resolver_match
        formattxt = resolvermatch.kwargs.get("format", "csv")
        # Instantiate the format object from base_formats in import_export
        try:
            format = getattr(base_formats, formattxt.upper())()
        except AttributeError:
            format = base_formats.CSV()

        try:
            self.before_dataset_export()
            dataset = (self.export_class).export(self.object_list)
        except AttributeError:
            dataset = self.get_dataset()

        filename = _("DV-{exportfilename}-{YMD_date}.{extension}").format(
            exportfilename=self.export_filename,
            YMD_date=timezone.now().strftime("%Y%m%d"),
            extension=format.get_extension(),
        )

        response = HttpResponse(
            getattr(dataset, formattxt), format.get_content_type() + ";charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="{f}"'.format(
            f=filename
        )
        return response

    def before_dataset_export(self):
        """
        Allows mixin-using classes to specify what to do to the export_class before exporting
        It's a noop by default
        """
        pass


class PaginatorMixin(object):
    paginate_by = 10
    paginate_orphans = 3

    def get_context_data(self, *args, **kwargs):
        context = super(PaginatorMixin, self).get_context_data(*args, **kwargs)
        # Re-create the filtered querystring from GET, drop page off it
        querydict = self.request.GET.copy()
        try:
            del querydict["page"]
        except Exception:
            pass
        context["filter_querystring"] = querydict.urlencode()
        return context
