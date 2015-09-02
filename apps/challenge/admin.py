from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from parler.admin import TranslatableAdmin

from .models import (
    Qualification, QualificationActivity, Session, SessionTimeSlot,
)

admin.site.register(SessionTimeSlot)
admin.site.register(Session)
admin.site.register(Qualification)


class QualificationActivityAdmin(TranslatableAdmin):
    list_display = ['category', 'name', 'missing_languages']
    list_display_links = ('name', )
    search_fields = ('translations__name', 'pk')

    def missing_languages(self, obj):
        missing_languages = list(
            set([l[0] for l in settings.LANGUAGES]) -
            set(obj.get_available_languages())
        )
        if missing_languages:
            return " | ".join(missing_languages)
        else:
            return '<img src="%s" />' % static('admin/img/icon-yes.gif')
    missing_languages.allow_tags = True

admin.site.register(QualificationActivity, QualificationActivityAdmin)
