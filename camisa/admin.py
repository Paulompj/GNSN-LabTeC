from django.contrib import admin

# Register your models here.
from .models import Camisa, CamisaLog

admin.site.register(Camisa)
admin.site.register(CamisaLog)
