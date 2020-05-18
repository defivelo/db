from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from parler.admin import TranslatableAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import MonthlyCantonalValidation, MonthlyCantonalValidationUrl


class MonthlyCantonalValidationUrlAdmin(TranslatableAdmin):
    list_display = ["url", "name", "missing_languages"]
    list_display_links = (
        "url",
        "name",
    )
    search_fields = ("translations__name", "pk")

    def missing_languages(self, obj):
        missing_languages = list(
            set([l[0] for l in settings.LANGUAGES]) - set(obj.get_available_languages())
        )
        if missing_languages:
            return " | ".join(missing_languages)
        else:
            return mark_safe('<img src="%s" />' % static("admin/img/icon-yes.svg"))


class MonthlyCantonalValidationAdmin(SimpleHistoryAdmin):
    pass


admin.site.register(MonthlyCantonalValidation, MonthlyCantonalValidationAdmin)
admin.site.register(MonthlyCantonalValidationUrl, MonthlyCantonalValidationUrlAdmin)
