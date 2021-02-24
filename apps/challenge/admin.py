# defivelo-intranet -- Outil métier pour la gestion du Défi Vélo
# Copyright (C) 2015, 2020 Didier Raboud <me+defivelo@odyx.org>
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
from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from parler.admin import TranslatableAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    AnnualStateSetting,
    HelperSessionAvailability,
    Qualification,
    QualificationActivity,
    Season,
    Session,
)
from .models.registration import Registration


class QualificationActivityAdmin(TranslatableAdmin):
    list_display = ["category", "name", "missing_languages"]
    list_display_links = ("name",)
    search_fields = ("translations__name", "pk")

    def missing_languages(self, obj):
        missing_languages = list(
            set([l[0] for l in settings.LANGUAGES]) - set(obj.get_available_languages())
        )
        if missing_languages:
            return " | ".join(missing_languages)
        else:
            return mark_safe('<img src="%s" />' % static("admin/img/icon-yes.svg"))


class SeasonAdmin(SimpleHistoryAdmin):
    pass


class SessionAdmin(SimpleHistoryAdmin):
    pass


class QualificationAdmin(SimpleHistoryAdmin):
    pass


class HelperSessionAvailabilityAdmin(SimpleHistoryAdmin):
    pass


class AnnualStateSettingAdmin(SimpleHistoryAdmin):
    pass


admin.site.register(QualificationActivity, QualificationActivityAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Qualification, QualificationAdmin)
admin.site.register(HelperSessionAvailability, HelperSessionAvailabilityAdmin)
admin.site.register(AnnualStateSetting, AnnualStateSettingAdmin)
admin.site.register(Registration)
