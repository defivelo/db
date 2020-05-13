from django.contrib import admin

from simple_history.admin import SimpleHistoryAdmin

from .models import MonthlyCantonalValidation


class MonthlyCantonalValidationAdmin(SimpleHistoryAdmin):
    pass


admin.site.register(MonthlyCantonalValidation, MonthlyCantonalValidationAdmin)
