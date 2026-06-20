from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    Patient,
    PricingRequest,
    PricingRequestFile,
    PricingRequestNote,
    PricingStatusHistory,
)

admin.site.register(Patient)
admin.site.register(PricingRequest)
admin.site.register(PricingRequestFile)
admin.site.register(PricingRequestNote)
admin.site.register(PricingStatusHistory)