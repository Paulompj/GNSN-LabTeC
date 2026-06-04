from django.contrib import admin

from .models import (
    Guarda,
    StatusGuarda,
    GuardaStatus,
    Sacramento,
    ResponsavelGuarda,
    PadrinhoGuarda,
)

admin.site.register(Guarda)
admin.site.register(StatusGuarda)
admin.site.register(GuardaStatus)
admin.site.register(Sacramento)
admin.site.register(ResponsavelGuarda)
admin.site.register(PadrinhoGuarda)
