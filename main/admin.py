from django.contrib import admin

# Register your models here.
from .models import AuthenticationCode, User, Video

admin.site.register(AuthenticationCode)
admin.site.register(User)
admin.site.register(Video)