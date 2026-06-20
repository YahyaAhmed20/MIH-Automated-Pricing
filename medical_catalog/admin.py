from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    Specialty,
    Procedure,
    Package,
    PackageAttachment,
)

admin.site.register(Specialty)
admin.site.register(Procedure)
admin.site.register(Package)
admin.site.register(PackageAttachment)