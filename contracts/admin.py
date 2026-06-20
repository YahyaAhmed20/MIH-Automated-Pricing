from django.contrib import admin

# Register your models here.

from .models import (
    ContractEntity,
    SubCompany,
    FinancialCategory,
    PriceList,
    Contract,
    CoverageCategory,
    CoverageRule,
    ProfessionalFeeRule,
    SpecialOffer,
    ContractPackage
)



admin.site.register(ContractEntity)
admin.site.register(SubCompany)
admin.site.register(FinancialCategory)
admin.site.register(PriceList)
admin.site.register(Contract)
admin.site.register(CoverageCategory)
admin.site.register(CoverageRule)
admin.site.register(ProfessionalFeeRule)
admin.site.register(SpecialOffer)
admin.site.register(ContractPackage)