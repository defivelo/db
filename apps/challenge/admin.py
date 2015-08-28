from django.contrib import admin

from .models import Session, SessionTimeSlot

admin.site.register(SessionTimeSlot)
admin.site.register(Session)
