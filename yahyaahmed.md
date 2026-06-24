التعديل ف الباكدج الاجل 
حته السيرش + الخانه + font cairo

في تحت كل شركه بيبقه في وصف صغير ب font صغير شويه 

حاجات ممكن تتأجل للنسخة 2

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




ده ملف credit_package_pricing  + view

{% extends 'frontend/base.html' %}

{% block page_title %}
الباكدجات الآجل
{% endblock %}

{% block content %}

<div class="card shadow border-0">

    <div class="card-header">
        <h4 class="mb-0">
            <i class="bi bi-box"></i>
            الباكدجات الآجل
        </h4>
    </div>

    <div class="card-body">

        <!-- ============================================ -->
        <!-- Form البحث والفلتر -->
        <!-- ============================================ -->
        <form method="get">

            <div class="row g-3 align-items-end">

                <div class="col-md-5">

                    <label class="form-label fw-bold text-muted small">
                        <i class="bi bi-building"></i>
                        الشركة
                    </label>

                    <select
                        name="company"
                        class="form-select form-select-lg"
                        onchange="this.form.submit()">

                        <option value="">
                            اختر الشركة
                        </option>

                        {% for company in companies %}

                        <option
                            value="{{ company.id }}"
                            {% if selected_company == company.id|stringformat:"s" %}
                            selected
                            {% endif %}
                        >
                            {{ company.name }}
                        </option>

                        {% endfor %}

                    </select>

                </div>

                <div class="col-md-5">

                    <label class="form-label fw-bold text-muted small">
                        <i class="bi bi-box"></i>
                        الباكدج
                    </label>

                    <select
                        name="package"
                        class="form-select form-select-lg"
                        onchange="this.form.submit()">

                        <option value="">
                            {% if packages %}
                                اختر الباكدج
                            {% else %}
                                اختر الشركة أولاً
                            {% endif %}
                        </option>

                        {% for cp in packages %}

                        <option
                            value="{{ cp.id }}"
                            {% if selected_package and selected_package.id == cp.id %}
                            selected
                            {% endif %}
                        >
                            {{ cp.package.name }}
                        </option>

                        {% endfor %}

                    </select>

                </div>

                <div class="col-md-2">

                    <a href="{% url 'credit_package_pricing' %}" class="btn btn-outline-secondary btn-lg w-100">
                        <i class="bi bi-arrow-counterclockwise"></i>
                        مسح
                    </a>

                </div>

            </div>

        </form>

    </div>

</div>

<!-- ============================================ -->
<!-- عرض تفاصيل الباكدج المختار -->
<!-- ============================================ -->
{% if selected_package %}

<div class="card shadow border-0 mt-4">

    <div class="card-header bg-primary text-white">

        <h5 class="mb-0">
            <i class="bi bi-info-circle"></i>
            تفاصيل الباكدج
        </h5>

    </div>

    <div class="card-body">

        <div class="row g-4">

            <div class="col-md-4">

                <label class="text-muted">
                    الشركة
                </label>

                <h6>
                    {{ selected_package.contract.entity.name }}
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    التخصص
                </label>

                <h6>
                    {{ selected_package.package.specialty.name }}
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    السعر
                </label>

                <h6 class="text-primary">
                    {{ selected_package.formatted_price }} ج.م
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    مدة الإقامة
                </label>

                <h6>
                    {{ selected_package.package.stay_duration|default:"-" }}
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    الكود
                </label>

                <h6>
                    {{ selected_package.package.code|default:"-" }}
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    الخصم الحالي
                </label>

                <h6>
                    <span class="badge bg-success">
                        {{ selected_package.formatted_discount }}%
                    </span>
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    السعر النقدي
                </label>

                <h6 class="text-success">
                    {{ selected_package.formatted_cash }} ج.م
                </h6>

            </div>

            <div class="col-md-4">

                <label class="text-muted">
                    اعتباراً من
                </label>

                <h6>
                    {{ selected_package.effective_from|date:"Y-m-d"|default:"-" }}
                </h6>

            </div>

            <div class="col-md-4">

                {% comment %} <label class="text-muted">
                    صالح حتى
                </label> {% endcomment %}

                <h6>
                    {{ selected_package.valid_until|date:"Y-m-d"|default:"-" }}
                </h6>

            </div>

            <!-- ✅ تحسين عرض الملاحظات -->
            <div class="col-md-4">

                <label class="text-muted">
                    ملاحظات الباكدج
                </label>

                <h6 style="white-space: pre-line;">
                    {% if selected_package.package.package_note %}
                        {{ selected_package.package.package_note }}
                    {% else %}
                        -
                    {% endif %}
                </h6>

            </div>

        </div>

    </div>

</div>

<!-- ============================================ -->
<!-- تخفيض السعر 🔥 -->
<!-- ============================================ -->

<div class="card shadow border-0 mt-4">

    <div class="card-header bg-success text-white">

        <h5 class="mb-0">
            <i class="bi bi-percent"></i>
            تخفيض السعر
        </h5>

    </div>

    <div class="card-body">

        <input
            type="hidden"
            id="base-price"
            value="{{ selected_package.total_before_discount|default:0 }}"
        >

        <input
            type="hidden"
            id="special-price"
            value="{{ selected_package.special_offer_price|default:0 }}"
        >

        <input
            type="hidden"
            id="cash-price"
            value="{{ selected_package.cash_price|default:0 }}"
        >

        <div class="row g-4">

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    الإجمالي بدون خصم
                </label>

                <input
                    class="form-control"
                    value="{{ selected_package.formatted_total_before }} ج.م"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    Special Offer
                </label>

                <input
                    class="form-control"
                    value="{{ selected_package.formatted_special_offer }}"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    Cash
                </label>

                <input
                    class="form-control"
                    value="{{ selected_package.formatted_cash }}"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    الخصم الحالي
                </label>

                <input
                    class="form-control"
                    value="{{ selected_package.formatted_discount }}%"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    معدل الخصم المقترح
                </label>

                <select
                    id="discount-select"
                    class="form-select">

                    <option value="5">5%</option>
                    <option value="10">10%</option>
                    <option value="15">15%</option>
                    <option value="20">20%</option>
                    <option value="25">25%</option>

                    {% if selected_package.special_offer_price %}
                        <option value="special">Special Offer</option>
                    {% endif %}

                    <option value="cash">Cash</option>

                </select>

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    السعر المقترح
                </label>

                <input
                    id="suggested-price"
                    class="form-control"
                    readonly
                >

            </div>

        </div>

        <!-- عرض الفرق المالي والوفر -->
        <div class="row g-4 mt-3">

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    السعر الحالي
                </label>

                <input
                    id="current-price"
                    class="form-control"
                    value="{{ selected_package.formatted_price }} ج.م"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    السعر المقترح
                </label>

                <input
                    id="suggested-price-display"
                    class="form-control"
                    readonly
                >

            </div>

            <div class="col-md-4">

                <label class="form-label fw-bold text-muted small">
                    الوفر
                </label>

                <input
                    id="savings-display"
                    class="form-control fw-bold"
                    readonly
                >

            </div>

        </div>

    </div>

</div>

<!-- ============================================ -->
<!-- جدول مقارنة الخصومات -->
<!-- ============================================ -->

<div class="card shadow border-0 mt-4">

    <div class="card-header bg-warning">

        <h5 class="mb-0">
            <i class="bi bi-table"></i>
            مقارنة الخصومات
        </h5>

    </div>

    <div class="card-body">

        <div class="table-responsive">

            <table class="table table-bordered table-hover">

                <thead class="table-light">

                    <tr>
                        <th>الخصم</th>
                        <th>السعر</th>
                    </tr>

                </thead>

                <tbody>

                    <tr>
                        <td><strong>5%</strong></td>
                        <td id="price5">-</td>
                    </tr>

                    <tr>
                        <td><strong>10%</strong></td>
                        <td id="price10">-</td>
                    </tr>

                    <tr>
                        <td><strong>15%</strong></td>
                        <td id="price15">-</td>
                    </tr>

                    <tr>
                        <td><strong>20%</strong></td>
                        <td id="price20">-</td>
                    </tr>

                    <tr>
                        <td><strong>25%</strong></td>
                        <td id="price25">-</td>
                    </tr>

                </tbody>

            </table>

        </div>

    </div>

</div>

<!-- ============================================ -->
<!-- Box المرفقات -->
<!-- ============================================ -->

<div class="card shadow border-0 mt-4">

    <div class="card-header bg-info text-white">

        <h5 class="mb-0">
            <i class="bi bi-paperclip"></i>
            المرفقات
        </h5>

    </div>

    <div class="card-body">

        {% if selected_package.approval_pdf %}

            <div class="alert alert-success mb-0">

                <strong>
                    <i class="bi bi-file-pdf"></i>
                    المرفقات:
                </strong>

                <hr>

                <pre class="mb-0" style="white-space: pre-wrap; word-wrap: break-word;">
{{ selected_package.approval_pdf }}
                </pre>

            </div>

        {% else %}

            <div class="alert alert-warning mb-0">

                <i class="bi bi-exclamation-triangle"></i>
                لا توجد مرفقات

            </div>

        {% endif %}

    </div>

</div>

{% endif %}

<!-- ============================================ -->
<!-- عرض جميع الباكدجات للشركة المختارة -->
<!-- ============================================ -->
{% if packages and not selected_package %}

<div class="card mt-4 shadow">

    <div class="card-header">
        <h5 class="mb-0">
            <i class="bi bi-list"></i>
            الباكدجات المتاحة
            <span class="badge bg-secondary ms-2">
                {{ packages|length }}
            </span>
        </h5>
    </div>

    <div class="card-body">

        <div class="table-responsive">

            <table class="table table-hover table-striped">

                <thead>
                    <tr>
                        <th>#</th>
                        <th>اسم الباكدج</th>
                        <th>السعر</th>
                        <th>الخصم</th>
                        <th>النقدي</th>
                    </tr>
                </thead>

                <tbody>

                {% for cp in packages %}

                    <tr>
                        <td>{{ forloop.counter }}</td>
                        <td>
                            <strong>{{ cp.package.name }}</strong>
                        </td>
                        <td>{{ cp.package_price|floatformat:2 }} ج.م</td>
                        <td>
                            {% if cp.current_discount_rate %}
                                {{ cp.current_discount_rate }}%
                            {% else %}
                                -
                            {% endif %}
                        </td>
                        <td>{{ cp.cash_price|floatformat:2|default:"-" }} ج.م</td>
                    </tr>

                {% endfor %}

                </tbody>

            </table>

        </div>

    </div>

</div>

{% endif %}

<!-- ============================================ -->
<!-- Script تخفيض السعر + جدول المقارنات -->
<!-- ============================================ -->
{% if selected_package %}
<script>
    function calculatePrice() {

        const basePrice = parseFloat(
            document.getElementById("base-price").value || 0
        );

        const discountValue =
            document.getElementById("discount-select").value;

        let result = basePrice;

        const specialPrice =
            parseFloat(
                document.getElementById("special-price").value || 0
            );

        const cashPrice =
            parseFloat(
                document.getElementById("cash-price").value || 0
            );

        let displayPrice = 0;
        let savings = 0;
        const currentPrice = parseFloat(
            document.getElementById("current-price").value.replace(/[^0-9.]/g, '') || 0
        );

        if (discountValue === "special") {
            result = specialPrice;
        }
        else if (discountValue === "cash") {
            result = cashPrice;
        }
        else {
            const discount = parseFloat(discountValue);
            result = basePrice * (1 - discount / 100);
        }

        const formattedResult = result.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        const displayResult = formattedResult + " ج.م";

        document.getElementById("suggested-price").value = displayResult;
        document.getElementById("suggested-price-display").value = displayResult;

        const resultNum = parseFloat(formattedResult);
        displayPrice = resultNum;
        savings = currentPrice - resultNum;

        const suggestedInput = document.getElementById("suggested-price-display");
        if (resultNum < currentPrice) {
            suggestedInput.className = "form-control text-success fw-bold";
        } else if (resultNum > currentPrice) {
            suggestedInput.className = "form-control text-danger fw-bold";
        } else {
            suggestedInput.className = "form-control";
        }

        const savingsInput = document.getElementById("savings-display");
        if (savings > 0) {
            savingsInput.value = savings.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + " ج.م";
            savingsInput.className = "form-control fw-bold text-success";
        } else if (savings < 0) {
            savingsInput.value = Math.abs(savings).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + " ج.م (خسارة)";
            savingsInput.className = "form-control fw-bold text-danger";
        } else {
            savingsInput.value = "0.00 ج.م";
            savingsInput.className = "form-control";
        }

    }

    document.addEventListener("DOMContentLoaded", function () {

        calculatePrice();

        document.getElementById("discount-select")
            .addEventListener("change", calculatePrice);

        const basePrice = parseFloat(
            document.getElementById("base-price").value || 0
        );

        [5, 10, 15, 20, 25].forEach(function(d) {
            const value = basePrice * (1 - d / 100);
            document.getElementById("price" + d).innerText =
                value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",") + " ج.م";
        });

    });
</script>
{% endif %}

{% endblock %}     
def credit_package_pricing(request):

    company_id = request.GET.get("company")
    package_id = request.GET.get("package")

    companies = (
        ContractEntity.objects
        .filter(
            contracts__contract_packages__isnull=False
        )
        .distinct()
        .order_by("name")
    )

    packages = ContractPackage.objects.none()

    selected_package = None

    if company_id:

        packages = (
            ContractPackage.objects
            .filter(
                contract__entity_id=company_id
            )
            .select_related(
                "package"
            )
            .order_by("package__name")
        )

    if package_id:

        selected_package = get_object_or_404(
            ContractPackage.objects.select_related(
                "package",
                "contract__entity",
                "package__specialty",
            ),
            id=package_id
        )

        # ✅ تنسيق الأرقام في الـ View (زي ما عملت في home)
        if selected_package:
            selected_package.formatted_price = f"{selected_package.package_price:,.2f}"
            selected_package.formatted_cash = f"{selected_package.cash_price:,.2f}" if selected_package.cash_price else "-"
            selected_package.formatted_total_before = f"{selected_package.total_before_discount:,.2f}" if selected_package.total_before_discount else "0.00"
            selected_package.formatted_special_offer = f"{selected_package.special_offer_price:,.2f}" if selected_package.special_offer_price else "-"
            selected_package.formatted_discount = f"{selected_package.current_discount_rate:,.2f}" if selected_package.current_discount_rate else "0.00"
            selected_package.formatted_current_price = f"{selected_package.package_price:,.2f}"

    return render(
        request,
        "frontend/credit_package_pricing.html",
        {
            "companies": companies,
            "packages": packages,
            "selected_package": selected_package,
            "selected_company": company_id,
        }
    )