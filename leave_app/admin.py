from django.contrib import admin
from .models import User, LeaveRequest, LeaveTransition

admin.site.register(User)
admin.site.register(LeaveRequest)
admin.site.register(LeaveTransition)
