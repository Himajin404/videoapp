from django.contrib import admin

# Register your models here.
from .models import AuthenticationCode

admin.site.register(AuthenticationCode)