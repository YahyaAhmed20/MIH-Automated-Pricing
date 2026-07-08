<datalist>
SEARCH
ثم شغل:

الاسم
 ده اسم المريض 

✅ الحل: أضف خاصية onkeyup في الـ HTML


python manage.py import_package_catalog APP.xlsx

ثم:

python manage.py migrate_contract_entities APP.xlsx

  الصفحة 1: 'ردود النموذج 1'
  الصفحة 2: 'DATA'
  الصفحة 3: 'الباكدجات'
  الصفحة 4: 'الواجهه'
  الصفحة 5: 'الشرح'
  الصفحة 6: '1'
  الصفحة 7: '2'
  الصفحة 8: '3'
  الصفحة 9: '4'
  الصفحة 10: '5'
  الصفحة 11: 'DATA خصومات الشركات'
  الصفحة 12: 'نسب خصومات الشركات'
  الصفحة 13: 'نسخة من DATA'
  الصفحة 14: 'packages '
  الصفحة 15: 'package price'
  الصفحة 16: 'Users'
  الصفحة 17: 'c packages'
  الصفحة 18: 'company '
  الصفحة 19: '6'
  الصفحة 20: '7'
  الصفحة 21: '8'
  الصفحة 22: '9'
  الصفحة 23: '10'
  الصفحة 24: '11'
  الصفحة 25: '12'
  الصفحة 26: 'fffffff'
  الصفحة 27: 'Draft'
  الصفحة 28: '13'
  الصفحة 29: '14'



❌ Authentication & Permissions
❌ Export Excel / PDF
❌ Notifications
❌ CRUD كامل للعقود والجهات
❌ إدارة المستخدمين




ف الباكيدج  ركز فيه  النقدي 


البطافات 





التخصص راجع عليه 

تخفيض السعر 


معدل الخصم المقترح بيقرا من الاجمالي 



الاجمالي بدون خصم
12,950

ضربنا الاتننين دول ف بعض 
معدل الخصم الحالي
5%


 السعر
12,303


بعد كده عايز اقلل السعر 
معدل الخصم المقترح مربوط special offer and cash and اسم الشركه and الاجمالي بدون خصم 



في اسم اسمه مصطففي ابو الفنتوج بيديني كزا id 




ركز بعد كده ع اسماء الشيتات 



def procedure_fees(request):

    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    fees = ProcedureFee.objects.all()

    if search:
        fees = fees.filter(
            Q(entity_name__icontains=search) |
            Q(financial_category__icontains=search)
        )

    # ✅ ✅ ✅ نجيب الـ fees للتصنيف المختار (للأتعاب فقط)
    fees_filtered = fees
    if category:
        fees_filtered = fees.filter(category=category)

    # ✅ ✅ ✅ نجيب كل الجهات (حتى لو مش عندها التصنيف المختار)
    entities = {}
    
    # ✅ نجيب كل الصفوف (بما فيها الصف الرئيسي) عشان ناخد discount_rate
    all_fees = fees.all()
    
    for fee in all_fees:
        key = f"{fee.entity_name}_{fee.financial_category}"
        
        if key not in entities:
            entities[key] = {
                "entity_name": fee.entity_name,
                "financial_category": fee.financial_category,
                "price_list": fee.price_list,
                "discount_rate": fee.discount_rate,  # ✅ من الصف الرئيسي
                "fees": {},
            }
        if fee.category:
            entities[key]["fees"][fee.category] = {
                "surgeon_fee": fee.surgeon_fee,
                "anesthesia_fee": fee.anesthesia_fee,
                "assistant_fee": fee.assistant_fee,
                "total_fee": fee.total_fee,
            }

    # ✅ ✅ ✅ تصحيح الـ discount_rate (لو "0" أو فارغ، نجيبه من الصف الرئيسي)
    for key, entity in entities.items():
        if entity["discount_rate"] in ["0", "", None]:
            # ✅ نجيب أول سجل للجهة دي مش "0"
            correct_fee = all_fees.filter(
                entity_name=entity["entity_name"],
                financial_category=entity["financial_category"]
            ).exclude(discount_rate__in=["0", "", None]).first()
            
            if correct_fee:
                entity["discount_rate"] = correct_fee.discount_rate

    # ✅ تصفية الجهات اللي عندها التصنيف المختار (لو اختار تصنيف)
    entities_list = []
    for key, entity in entities.items():
        # ✅ لو في تصنيف محدد، نعرض بس الجهات اللي عندها التصنيف ده
        if category and category not in entity["fees"]:
            continue
            
        entity_data = {
            "entity_name": entity["entity_name"],
            "financial_category": entity["financial_category"],
            "price_list": entity["price_list"],
            "discount_rate": entity["discount_rate"],
            "fees": entity["fees"],
        }
        if category and category in entity["fees"]:
            fee_data = entity["fees"][category]
            entity_data["selected_surgeon_fee"] = fee_data["surgeon_fee"]
            entity_data["selected_anesthesia_fee"] = fee_data["anesthesia_fee"]
            entity_data["selected_assistant_fee"] = fee_data["assistant_fee"]
            entity_data["selected_total_fee"] = fee_data["total_fee"]
        entities_list.append(entity_data)

    # ✅ التصنيفات الفريدة
    categories = (
        ProcedureFee.objects
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "frontend/procedure_fees.html",
        {
            "entities": entities_list,
            "categories": categories,
            "selected_category": category,
            "search": search,
        }
    )




    {% extends "frontend/base.html" %}
{% load humanize %}

{% block page_title %}
احتساب أتعاب العملية
{% endblock %}

{% block content %}

<div class="container-fluid">

    <!-- ✅ Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      
        <div>
            <span class="badge bg-primary rounded-pill fs-6 px-3 py-2">
                <i class="fas fa-calendar-alt me-1"></i>
                آخر تحديث: {% now "Y-m-d" %}
            </span>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ شريط البحث والفلاتر -->
    <!-- ============================================ -->
    <div class="card shadow-sm border-0 mb-4 hover-shadow">

        <div class="card-header bg-gradient-primary text-white">
            <h5 class="mb-0">
                <i class="fas fa-sliders-h"></i>
                البحث والفلاتر
            </h5>
        </div>

        <div class="card-body">
            <form method="get" id="searchForm">
                <div class="row g-3 align-items-end">
                    <div class="col-md-5">
                        <label class="form-label fw-bold small text-muted">
                            <i class="fas fa-search"></i> بحث
                        </label>
                        <div class="input-group">
                            <span class="input-group-text bg-light border-0">
                                <i class="fas fa-search text-primary"></i>
                            </span>
                            <input
                                id="search"
                                name="search"
                                class="form-control form-control-lg border-0 shadow-sm"
                                list="entityList"
                                value="{{ search }}"
                                onchange="this.form.submit()"
                                onkeydown="if(event.key === 'Enter') this.form.submit()"
                                placeholder="ابحث باسم الجهة أو الفئة المالية..."
                                autocomplete="off">
                            <datalist id="entityList">
                                {% for entity in entities %}
                                    <option value="{{ entity.entity_name }}">
                                    <option value="{{ entity.financial_category }}">
                                {% endfor %}
                            </datalist>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label fw-bold small text-muted">
                            <i class="fas fa-layer-group"></i> التصنيف
                        </label>
                        <div class="input-group">
                            <span class="input-group-text bg-light border-0">
                                <i class="fas fa-layer-group text-primary"></i>
                            </span>
                            <select
                                name="category"
                                class="form-select form-select-lg border-0 shadow-sm"
                                onchange="this.form.submit()">
                                <option value="">كل التصنيفات</option>
                                {% for cat in categories %}
                                    <option
                                        value="{{ cat }}"
                                        {% if selected_category == cat %}selected{% endif %}>
                                        {{ cat }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <label class="form-label fw-bold small text-muted">&nbsp;</label>
                        <a href="{% url 'procedure_fees' %}" class="btn btn-outline-secondary btn-lg w-100 shadow-sm">
                            <i class="fas fa-undo me-1"></i> مسح الكل
                        </a>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-12">
                        {% if search or selected_category %}
                       
                        {% endif %}
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ عرض البطاقات -->
    <!-- ============================================ -->
    <div class="row g-4">

        {% for entity in entities %}

        <div class="col-md-6 col-lg-4">

            <div class="card shadow-sm border-0 hover-shadow h-100">

                <div class="card-header bg-primary text-white">

                    <h5 class="mb-0">
                        <i class="fas fa-building me-2"></i>
                        {{ entity.entity_name|default:"غير محدد" }}
                    </h5>

                </div>

                <div class="card-body">

                    <!-- ✅ معلومات الجهة -->
                    <div class="mb-3">
                        <p class="mb-1">
                            <strong>الفئة المالية:</strong>
                            <span class="badge bg-secondary">{{ entity.financial_category|default:"-" }}</span>
                        </p>
                        <p class="mb-1">
                            <strong>قائمة الأسعار:</strong>
                            {{ entity.price_list|default:"-" }}
                        </p>
                        <p class="mb-0">
                            <strong>معدل الخصم:</strong>
                            <span class="badge bg-success">{{ entity.discount_rate|default:"-" }}</span>
                        </p>
                    </div>

                    <hr>

                    <!-- ✅ الأتعاب حسب التصنيف -->
                    <h6 class="fw-bold text-muted mb-3">
                        <i class="fas fa-money-bill-wave me-1"></i>
                        الأتعاب
                        {% if selected_category %}
                        <span class="badge bg-info">{{ selected_category }}</span>
                        {% endif %}
                    </h6>

                    {% if selected_category %}

                    <div class="table-responsive">
                        <table class="table table-sm table-bordered mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>النوع</th>
                                    <th class="text-end">القيمة</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>جراح</td>
                                    <td class="text-end fw-bold">
                                        {{ entity.selected_surgeon_fee|floatformat:0|default:"-" }}
                                    </td>
                                </tr>
                                <tr>
                                    <td>تخدير</td>
                                    <td class="text-end fw-bold">
                                        {{ entity.selected_anesthesia_fee|floatformat:0|default:"-" }}
                                    </td>
                                </tr>
                                <tr>
                                    <td>مساعد</td>
                                    <td class="text-end fw-bold">
                                        {{ entity.selected_assistant_fee|floatformat:0|default:"-" }}
                                    </td>
                                </tr>
                                <tr class="table-success">
                                    <td><strong>الإجمالي</strong></td>
                                    <td class="text-end fw-bold text-success">
                                        {{ entity.selected_total_fee|floatformat:0|default:"-" }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    {% else %}

                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle me-1"></i>
                        اختر تصنيفاً لعرض الأتعاب
                    </div>

                    {% endif %}

                </div>

            </div>

        </div>

        {% empty %}

        <div class="col-12">
            <div class="alert alert-info text-center py-5">
                <i class="fas fa-inbox fa-3x d-block mb-3 text-muted"></i>
                <h5 class="text-muted">لا توجد نتائج</h5>
                <p class="text-muted small">حاول تغيير كلمات البحث أو اختيار تصنيف آخر</p>
            </div>
        </div>

        {% endfor %}

    </div>

</div>

<!-- ============================================ -->
<!-- ✅ CSS تحسينات -->
<!-- ============================================ -->
<style>
    .bg-gradient-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .hover-shadow {
        transition: all 0.3s ease;
    }

    .hover-shadow:hover {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px);
    }

    .card {
        border-radius: 1rem;
        overflow: hidden;
    }

    .card-header {
        border-radius: 0 !important;
    }

    .badge {
        font-weight: 500;
    }

    .input-group-text {
        border-radius: 0.5rem 0 0 0.5rem;
        background: #f8f9fa;
    }

    .form-control,
    .form-select {
        border-radius: 0 0.5rem 0.5rem 0;
    }

    .form-control:focus,
    .form-select:focus {
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        border-color: #667eea;
    }

    @media (max-width: 768px) {
        .card-body {
            padding: 1rem;
        }
        .badge.fs-6 {
            font-size: 0.85rem !important;
        }
    }
</style>

{% endblock %}