from django.contrib import admin

from .models import Qualification, Session, SessionTimeSlot

admin.site.register(SessionTimeSlot)
admin.site.register(Session)
admin.site.register(Qualification)
