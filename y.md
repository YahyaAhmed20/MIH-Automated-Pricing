{% extends 'frontend/base.html' %}
{% block page_title %}
الباكدجات الآجل
{% endblock %}

{% block content %}
<style>
    /* ============================================ */
    /* ✅ تحسينات UI من صفحة البحث */
    /* ============================================ */
    
    /* ===== Filter Card ===== */
    .filter-card {
        border-radius: 16px;
        border: none;
        background: #fff;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
    }
    
    .filter-card .card-body {
        padding: 1.25rem;
    }
    
    .filter-card .form-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #495057;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    
    .filter-card .form-select,
    .filter-card .form-control {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        font-size: 0.85rem;
        padding: 0.4rem 0.8rem;
        transition: all 0.3s ease;
        background: #fff;
    }
    
    .filter-card .form-select:focus,
    .filter-card .form-control:focus {
        border-color: #0d6efd;
        box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.1);
    }
    
    .filter-card .btn-filter {
        border-radius: 10px;
        padding: 0.4rem 1.2rem;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.3s ease;
    }
    
    .filter-card .btn-filter:hover {
        transform: translateY(-2px);
    }
    
    /* ===== Search Box ===== */
    .search-wrapper {
        position: relative;
    }
    .search-wrapper .form-control {
        padding-right: 45px;
    }
    .search-wrapper .search-icon {
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        color: #adb5bd;
        font-size: 1.1rem;
        pointer-events: none;
    }
    
    /* ===== Results Count ===== */
    .results-count {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        border: 1px solid #e9ecef;
    }
    
    .results-count .count-badge {
        background: #0d6efd;
        color: #fff;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    /* ===== Custom Table ===== */
    .custom-table {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    }
    
    .custom-table thead {
        background: linear-gradient(135deg, #1a237e, #0d47a1);
        color: #fff;
    }
    
    .custom-table thead th {
        padding: 0.75rem 1rem;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: none;
        white-space: nowrap;
    }
    
    .custom-table tbody td {
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        vertical-align: middle;
        border-bottom: 1px solid #f1f3f5;
    }
    
    .custom-table tbody tr {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .custom-table tbody tr:hover {
        background: #f8f9fa;
    }
    
    .custom-table tbody tr:last-child td {
        border-bottom: none;
    }
    
    .package-name {
        font-weight: 600;
        color: #1a1a2e;
    }
    .package-price {
        font-weight: 700;
        color: #0d6efd;
        font-size: 1.05rem;
    }
    
    /* ===== Badges ===== */
    .badge-code {
        background: linear-gradient(135deg, #0dcaf0, #0d6efd) !important;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.7rem;
        color: white !important;
    }
    .badge-specialty {
        background: linear-gradient(135deg, #0dcaf0, #0d6efd) !important;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.7rem;
        color: white !important;
    }
    .specialty-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
        background: #e3f2fd;
        color: #0d6efd;
    }
    
    /* ===== Alert ===== */
    .alert-custom {
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1rem;
    }
    
    .alert-custom .badge {
        font-size: 0.75rem;
    }
    
    /* ===== No Results ===== */
    .no-results {
        text-align: center;
        padding: 4rem 1rem;
        background: #f8f9fa;
        border-radius: 16px;
    }
    
    .no-results i {
        font-size: 4rem;
        color: #dee2e6;
        margin-bottom: 1rem;
    }
    
    /* ===== Info Cards ===== */
    .info-card {
        border-radius: 16px;
        padding: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #e9ecef;
        height: 100%;
        background: #fff;
        position: relative;
        overflow: hidden;
    }
    
    .info-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #0d6efd, #0dcaf0);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .info-card:hover::before {
        opacity: 1;
    }
    
    .info-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.1);
        border-color: #0d6efd;
    }
    
    .info-card .card-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #495057;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .info-card .card-title i {
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }
    
    .info-item {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #f1f3f5;
        font-size: 0.85rem;
        transition: background 0.2s ease;
        border-radius: 4px;
        padding: 6px 8px;
    }
    
    .info-item:hover {
        background: #f8f9fa;
    }
    
    .info-item:last-child {
        border-bottom: none;
    }
    
    .info-item .label {
        color: #6c757d;
        font-weight: 500;
        font-size: 0.8rem;
    }
    
    .info-item .value {
        font-weight: 600;
        color: #212529;
        text-align: left;
        word-break: break-word;
        max-width: 60%;
        font-size: 0.85rem;
    }
    
    /* ===== أنيميشن دخول الصفحة ===== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fadeInUp 0.6s ease forwards;
    }
    
    /* ============================================ */
    /* ✅ تحسينات الموبايل */
    /* ============================================ */
    @media (max-width: 768px) {
        .custom-table {
            font-size: 0.75rem;
        }
        
        .custom-table thead th,
        .custom-table tbody td {
            padding: 0.5rem 0.5rem;
        }
        
        .package-price {
            font-size: 0.9rem;
        }
        
        .badge-code,
        .badge-specialty {
            font-size: 0.6rem;
            padding: 0.2rem 0.5rem;
        }
        
        .filter-card .card-body {
            padding: 1rem;
        }
        
        .filter-card .form-select,
        .filter-card .form-control {
            font-size: 0.8rem;
            padding: 0.3rem 0.6rem;
        }
        
        .results-count {
            flex-direction: column;
            align-items: flex-start !important;
            gap: 0.5rem;
        }
        
        .info-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 2px;
            padding: 4px 6px;
        }
        
        .info-item .value {
            max-width: 100%;
            width: 100%;
        }
        
        .row.g-4 > .col-md-4,
        .row.g-4 > .col-md-3,
        .row.g-4 > .col-md-2 {
            flex: 0 0 50%;
            max-width: 50%;
        }
    }
    
    @media (max-width: 576px) {
        .custom-table {
            font-size: 0.65rem;
        }
        
        .custom-table thead th,
        .custom-table tbody td {
            padding: 4px 3px;
        }
        
        .package-price {
            font-size: 0.8rem;
        }
        
        .package-name {
            font-size: 0.75rem;
        }
        
        .badge-code,
        .badge-specialty {
            font-size: 0.5rem;
            padding: 0.15rem 0.35rem;
        }
        
        .filter-card .card-body {
            padding: 0.75rem;
        }
        
        .filter-card .form-select,
        .filter-card .form-control {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
        }
        
        .row.g-4 > .col-md-4,
        .row.g-4 > .col-md-3,
        .row.g-4 > .col-md-2 {
            flex: 0 0 100%;
            max-width: 100%;
        }
    }
</style>

<!-- ============================================ -->
<!-- ✅ الكارد الرئيسي -->
<!-- ============================================ -->
<div class="card shadow border-0 fade-in">
    <div class="card-header" style="background: linear-gradient(135deg, #0dcaf0, #0d6efd); color: #fff;">
        <div class="d-flex justify-content-between align-items-center">
            <h4 class="mb-0 d-flex align-items-center">
                <i class="bi bi-box me-2"></i>
                الباكدجات الآجل
            </h4>
            <div class="d-flex gap-2">
                <a href="{% url 'cash_packages' %}" class="btn btn-light">
                    <i class="bi bi-cash-stack me-2"></i>
                    الباكدجات النقدية
                </a>
                <a href="{% url 'packages_price_list' %}" class="btn btn-warning text-dark">
                    <i class="bi bi-list-ul me-2"></i>
                    عرض بقائمة الأسعار
                </a>
            </div>
        </div>
    </div>

    <div class="card-body">
        <!-- ============================================ -->
        <!-- ✅ Form البحث -->
        <!-- ============================================ -->
        <form id="search-form" method="get" action="{% url 'credit_package_pricing' %}">
            <div class="filter-card">
                <div class="card-body">
                    <div class="row g-3">
                        <!-- ✅ الشركة -->
                        <div class="col-md-3">
                            <label class="form-label">
                                <i class="bi bi-building"></i>
                                الشركة
                            </label>
                            <div class="search-wrapper">
                                <input
                                    type="text"
                                    name="company_search"
                                    id="company-search-input"
                                    class="form-control"
                                    placeholder="ابحث عن شركة..."
                                    autocomplete="off"
                                    list="company-list"
                                    onchange="handleCompanySearch(this)"
                                    value="{{ company_search }}"
                                >
                                <i class="bi bi-search search-icon"></i>
                                <datalist id="company-list">
                                    {% for company in companies %}
                                        <option value="{{ company.name }}" data-id="{{ company.id }}">
                                    {% endfor %}
                                </datalist>
                                <input type="hidden" name="company" id="selected-company-id" value="{{ selected_company.id|default:'' }}">
                            </div>
                            {% if selected_company %}
                                <small class="text-success mt-1 d-block">
                                    <i class="bi bi-check-circle-fill"></i>
                                    {{ selected_company.name }}
                                </small>
                            {% endif %}
                        </div>

                        <!-- ✅ التخصص -->
                        <div class="col-md-3">
                            <label class="form-label">
                                <i class="bi bi-star"></i>
                                التخصص
                            </label>
                            <select
                                name="specialty"
                                id="specialty-select"
                                class="form-select"
                                onchange="this.form.submit()"
                                {% if not selected_company %}disabled{% endif %}
                            >
                                <option value="">
                                    {% if selected_company %}
                                        جميع التخصصات
                                    {% else %}
                                        اختر الشركة أولاً
                                    {% endif %}
                                </option>
                                {% for specialty in specialties %}
                                <option
                                    value="{{ specialty.id }}"
                                    {% if selected_specialty|stringformat:"s" == specialty.id|stringformat:"s" %}
                                    selected
                                    {% endif %}
                                >
                                    {{ specialty.name }}
                                </option>
                                {% endfor %}
                            </select>
                            {% if selected_company and specialties %}
                                <small class="text-muted mt-1 d-block">
                                    <i class="bi bi-info-circle"></i>
                                    {{ specialties|length }} تخصص
                                </small>
                            {% endif %}
                        </div>

                        <!-- ✅ الباكدج -->
                        <div class="col-md-3">
                            <label class="form-label">
                                <i class="bi bi-box"></i>
                                الباكدج
                            </label>
                            <div class="search-wrapper">
                                <input
                                    type="text"
                                    name="package_search"
                                    id="package-search-input"
                                    class="form-control"
                                    placeholder="ابحث عن باكدج..."
                                    autocomplete="off"
                                    list="package-list"
                                    onchange="handlePackageSearch(this)"
                                    value="{{ package_search }}"
                                    {% if not selected_company %}disabled{% endif %}
                                >
                                <i class="bi bi-search search-icon"></i>
                                <datalist id="package-list">
                                    {% for cp in packages %}
                                        <option value="{{ cp.package.name }}" data-id="{{ cp.id }}" data-company="{{ cp.contract.entity.id }}">
                                    {% endfor %}
                                </datalist>
                                <input type="hidden" name="package" id="selected-package-id" value="{{ selected_package.id|default:'' }}">
                            </div>
                            {% if selected_company and packages %}
                                <small class="text-muted mt-1 d-block">
                                    <i class="bi bi-info-circle"></i>
                                    {{ packages|length }} باكدج
                                </small>
                            {% endif %}
                        </div>

                        <!-- ✅ أزرار -->
                        <div class="col-md-3">
                            <label class="form-label">
                                &nbsp;
                            </label>
                            <div class="d-flex gap-2">
                                <button class="btn btn-primary flex-grow-1 btn-filter" type="submit">
                                    <i class="bi bi-search me-1"></i>
                                    بحث
                                </button>
                                <a href="{% url 'credit_package_pricing' %}" class="btn btn-outline-secondary btn-filter">
                                    <i class="bi bi-arrow-counterclockwise"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </form>

        <!-- ============================================ -->
        <!-- ✅ عرض التخصصات المتاحة -->
        <!-- ============================================ -->
        {% if selected_company and specialties %}
        <div class="filter-card" style="background: #f8f9fc; border: 1px solid #e9ecef;">
            <div class="card-body py-2">
                <div class="d-flex flex-wrap align-items-center gap-2">
                    <span class="fw-bold text-muted small">
                        <i class="bi bi-tags"></i>
                        التخصصات المتاحة:
                    </span>
                    {% for specialty in specialties %}
                        <span class="specialty-badge">
                            <i class="bi bi-star-fill" style="font-size: 0.6rem;"></i>
                            {{ specialty.name }}
                        </span>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- ============================================ -->
        <!-- ✅ عرض تفاصيل الباكدج المختار -->
        <!-- ============================================ -->
        {% if selected_package %}
        <div class="card shadow border-0 mt-4 fade-in">
            <div class="card-header" style="background: linear-gradient(135deg, #0dcaf0, #0d6efd); color: #fff;">
                <h5 class="mb-0 d-flex align-items-center">
                    <i class="bi bi-info-circle me-2"></i>
                    معلومات الباكدج
                    <span class="badge bg-light text-dark ms-3">
                        <i class="bi bi-tag"></i>
                        {{ selected_package.package.code|default:"بدون كود" }}
                    </span>
                    {% if selected_package.package.specialty %}
                    <span class="badge bg-warning text-dark ms-2">
                        <i class="bi bi-star"></i>
                        {{ selected_package.package.specialty.name }}
                    </span>
                    {% endif %}
                </h5>
            </div>

            <div class="card-body">
                <div class="row g-4">
                    <!-- الشركة -->
                    <div class="col-md-4 col-lg-3">
                        <div class="info-card">
                            <label><i class="bi bi-building"></i> الشركة</label>
                            <div class="value">{{ selected_package.contract.entity.name }}</div>
                        </div>
                    </div>

                    <!-- اسم الباكدج -->
                    <div class="col-md-8 col-lg-5">
                        <div class="info-card">
                            <label><i class="bi bi-tag"></i> اسم الباكدج</label>
                            <div class="value text-primary">{{ selected_package.package.name }}</div>
                        </div>
                    </div>

                    <!-- التخصص -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-star"></i> التخصص</label>
                            <div class="value">{{ selected_package.package.specialty.name }}</div>
                        </div>
                    </div>

                    <!-- السعر -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-currency-pound"></i> السعر</label>
                            <div class="value text-primary">{{ selected_package.formatted_price }} ج.م</div>
                        </div>
                    </div>

                    <!-- مدة الإقامة -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-clock"></i> مدة الإقامة</label>
                            <div class="value">{{ selected_package.package.stay_duration|default:"-" }}</div>
                        </div>
                    </div>

                    <!-- الكود -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-upc-scan"></i> الكود</label>
                            <div class="value">{{ selected_package.package.code|default:"-" }}</div>
                        </div>
                    </div>

                    <!-- اعتباراً من -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-calendar-plus"></i> اعتباراً من</label>
                            <div class="value">{{ selected_package.effective_from|date:"Y-m-d"|default:"-" }}</div>
                        </div>
                    </div>

                    <!-- صالح حتى -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-calendar-minus"></i> صالح حتى</label>
                            <div class="value">{{ selected_package.valid_until|date:"Y-m-d"|default:"-" }}</div>
                        </div>
                    </div>

                    <!-- الحالة -->
                    <div class="col-md-4 col-lg-2">
                        <div class="info-card">
                            <label><i class="bi bi-check-circle"></i> الحالة</label>
                            <div class="value">
                                {% if selected_package.is_expired %}
                                    <span class="badge bg-danger">
                                        <i class="bi bi-exclamation-circle"></i> منتهي
                                    </span>
                                {% else %}
                                    <span class="badge bg-success">
                                        <i class="bi bi-check-circle"></i> ساري
                                    </span>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- ملاحظات الباكدج -->
                    <div class="col-md-12">
                        <div class="info-card">
                            <label><i class="bi bi-pencil"></i> ملاحظات الباكدج</label>
                            <div id="package-notes" style="padding: 4px 0; white-space: pre-wrap; line-height: 1.8;">
                                {% if selected_package.package.package_note %}
                                    {{ selected_package.package.package_note|linebreaksbr }}
                                {% else %}
                                    <span class="text-muted">لا توجد ملاحظات</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ============================================ -->
        <!-- ✅ التسعير والخصومات -->
        <!-- ============================================ -->
        <div class="card shadow border-0 mt-4 fade-in">
        <div class="card-header" style="background: linear-gradient(135deg, #0dcaf0, #0d6efd); color: #fff;">
                <h5 class="mb-0 d-flex align-items-center">
                    <i class="bi bi-cash-stack me-2"></i>
                    تخفيض التكلفة
                    <span class="badge bg-light text-dark ms-3">
                        <i class="bi bi-percent"></i>
                        خصم ديناميكي
                    </span>
                </h5>
            </div>

            <div class="card-body">
                <!-- Hidden Fields -->
                <input type="hidden" id="base-price" value="{{ selected_package.total_before_discount|default:0 }}">
                <input type="hidden" id="special-price" value="{{ selected_package.special_offer_price|default:0 }}">
                <input type="hidden" id="cash-price" value="{{ selected_package.cash_price|default:0 }}">
                <input type="hidden" id="current-price-value" value="{{ selected_package.package_price|default:0 }}">
                <input type="hidden" id="suggested-price-value" value="{{ selected_package.suggested_price|default:0 }}">

                <div class="row g-4">
                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-coin"></i> السعر الحالي</label>
                            <div class="value text-primary">{{ selected_package.formatted_price }} ج.م</div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-calculator"></i> الإجمالي (بدون خصم)</label>
                            <div class="value">{{ selected_package.formatted_total_before }} ج.م</div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-list-ul"></i> قائمة الأسعار</label>
                            <div class="value">{{ selected_package.price_list_applied|default:'-' }}</div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-percent"></i> معدل الخصم الحالي</label>
                            <div class="value">{{ selected_package.current_discount_label }}</div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-sliders2"></i> معدل الخصم المقترح</label>
                            <select id="discount-select" class="form-select">
                                {% if selected_package.suggested_discount_rate %}
                                <option value="{{ selected_package.suggested_discount_rate }}" selected>
                                    العقد الحالي ({{ selected_package.formatted_suggested_discount }})
                                </option>
                                {% endif %}
                                <option value="5">5%</option>
                                <option value="10">10%</option>
                                <option value="15">15%</option>
                                <option value="20">20%</option>
                                <option value="25">25%</option>
                            </select>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-tag"></i> السعر المقترح</label>
                            <div id="suggested-price-display" class="value text-success">
                                {{ selected_package.formatted_suggested_price }}
                            </div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="info-card">
                            <label><i class="bi bi-gift"></i> قيمة التخفيض</label>
                            <div id="savings-display" class="value text-danger">
                                {{ selected_package.formatted_discount_value }}
                            </div>
                        </div>
                    </div>

                    <div class="col-md-8">
                        <div class="alert alert-info mb-0">
                            <strong><i class="bi bi-info-circle"></i> ملاحظات الأسعار</strong>
                            <hr class="my-2">
                            <div class="row">
                                <div class="col-md-6">
                                    <i class="bi bi-star"></i>
                                    <strong>أقل سعر أجل (Special Offer):</strong>
                                    <span class="fw-bold">{{ selected_package.formatted_special_offer }} ج.م</span>
                                    {% if selected_package.special_offer_company %}
                                        <br>
                                        <small class="text-success">
                                            <i class="bi bi-building"></i>
                                            {{ selected_package.special_offer_company }}
                                        </small>
                                    {% endif %}
                                </div>
                                <div class="col-md-6">
                                    <i class="bi bi-cash"></i>
                                    <strong>السعر النقدي:</strong>
                                    <span class="fw-bold">{{ selected_package.formatted_cash }} ج.م</span>
                                </div>
                            </div>
                            <hr class="my-2">
                            <small class="text-muted">
                                <i class="bi bi-info-circle"></i>
                                تغيير نسبة الخصم يحسب السعر الجديد فقط، ولا يتم حفظ أي بيانات.
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ============================================ -->
        <!-- ✅ جدول مقارنة الخصومات -->
        <!-- ============================================ -->
        <div class="card shadow border-0 mt-4 fade-in">
            <div class="card-header" style="background: linear-gradient(135deg, #0dcaf0, #0d6efd); color: #fff;">
                <h5 class="mb-0 d-flex align-items-center">
                    <i class="bi bi-table me-2"></i>
                    معدلات الخصم المقترحة
                    <span class="badge bg-light text-dark ms-3">
                        <i class="bi bi-arrow-left-right"></i>
                        مقارنة
                    </span>
                </h5>
            </div>

            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered table-hover align-middle">
                        <thead>
                            <tr>
                                <th>معدل الخصم</th>
                                <th>السعر المقترح</th>
                                <th>قيمة التخفيض</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><span class="badge bg-primary">5%</span></td><td id="price5">-</td><td id="saving5">-</td></tr>
                            <tr><td><span class="badge bg-info">10%</span></td><td id="price10">-</td><td id="saving10">-</td></tr>
                            <tr><td><span class="badge bg-success">15%</span></td><td id="price15">-</td><td id="saving15">-</td></tr>
                            <tr><td><span class="badge bg-warning text-dark">20%</span></td><td id="price20">-</td><td id="saving20">-</td></tr>
                            <tr><td><span class="badge bg-danger">25%</span></td><td id="price25">-</td><td id="saving25">-</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ============================================ -->
        <!-- ✅ المرفقات -->
        <!-- ============================================ -->
        <div class="card shadow border-0 mt-4 fade-in">
            <div class="card-header" style="background: linear-gradient(135deg, #0dcaf0, #0d6efd); color: #fff;">
                <h5 class="mb-0 d-flex align-items-center">
                    <i class="bi bi-paperclip me-2"></i>
                    المرفقات
                    <span class="badge bg-light text-dark ms-3">
                        <i class="bi bi-file-earmark"></i>
                        {% if selected_package.approval_pdf %}مرفق{% else %}لا يوجد{% endif %}
                    </span>
                </h5>
            </div>

            <div class="card-body">
                {% if selected_package.approval_pdf %}
                    <div class="alert alert-success mb-0">
                        <strong><i class="bi bi-file-pdf"></i> المرفقات:</strong>
                        <hr class="my-2">
                        <pre class="mb-0" style="white-space: pre-wrap; word-wrap: break-word; font-size: 0.9rem;">{{ selected_package.approval_pdf }}</pre>
                    </div>
                {% else %}
                    <div class="alert alert-warning mb-0 text-center py-4">
                        <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                        <h6 class="mt-2">لا توجد مرفقات</h6>
                    </div>
                {% endif %}
            </div>
        </div>

        {% endif %}

        <!-- ============================================ -->
        <!-- ✅ عرض جميع الباكدجات للشركة المختارة -->
        <!-- ============================================ -->
        {% if packages and not selected_package %}
        <div id="packages-list" class="fade-in mt-4">
            <!-- ✅ عدد النتائج -->
            <div class="results-count d-flex justify-content-between align-items-center mb-3">
                <div>
                    <span class="count-badge">{{ packages|length }}</span>
                    <span class="text-muted small ms-1">باكدج</span>
                </div>
                <div>
                    <span class="text-muted small">
                        <i class="bi bi-building me-1"></i>
                        {{ selected_company.name }}
                    </span>
                </div>
            </div>

            <div class="table-responsive">
                <table class="table table-hover mb-0 custom-table">
                    <thead>
                        <tr>
                            <th style="width: 50px;">#</th>
                            <th>اسم الباكدج</th>
                            <th>الكود</th>
                            <th>التخصص</th>
                            <th>الشركة</th>
                            <th class="text-end">صافي السعر</th>
                            <th>معدل الخصم</th>
                            <th>الحالة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for cp in packages %}
                        <tr onclick="window.location.href='?company={{ selected_company.id }}&package={{ cp.id }}&company_search={{ company_search }}&package_search={{ package_search }}&specialty={{ selected_specialty }}'">
                            <td>{{ forloop.counter }}</td>
                            <td class="package-name">{{ cp.package.name }}</td>
                            <td>
                                <span class="badge badge-code">{{ cp.package.code|default:"-" }}</span>
                            </td>
                            <td>
                                {% if cp.package.specialty %}
                                    <span class="badge badge-specialty">{{ cp.package.specialty.name }}</span>
                                {% else %}
                                    <span class="badge badge-code">-</span>
                                {% endif %}
                            </td>
                            <td>{{ cp.contract.entity.name }}</td>
                            <td class="text-end package-price">{{ cp.formatted_price }} ج.م</td>
                            <td>
                                {% if cp.formatted_discount %}
                                    <span class="badge badge-specialty">{{ cp.formatted_discount }}</span>
                                {% else %}
                                    <span class="badge badge-code">-</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if cp.is_expired %}
                                    <span class="badge bg-danger">منتهي</span>
                                {% else %}
                                    <span class="badge bg-success">ساري</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}

        <!-- ============================================ -->
        <!-- ✅ لو مفيش نتائج -->
        <!-- ============================================ -->
        {% if not packages and not selected_package %}
        <div class="no-results mt-4">
            <i class="bi bi-box"></i>
            <h5 class="text-muted">
                {% if selected_company %}
                    لا توجد باكدجات لهذه الشركة
                {% else %}
                    اختر شركة لعرض الباكدجات
                {% endif %}
            </h5>
            <p class="text-muted small">استخدم الفلاتر أعلاه للبحث</p>
        </div>
        {% endif %}
    </div>
</div>

<!-- ============================================ -->
<!-- ✅ JavaScript الرئيسي -->
<!-- ============================================ -->
<script>
// ============================================================
// ✅ معالجة بحث الشركة
// ============================================================
function handleCompanySearch(input) {
    const filter = input.value.toLowerCase().trim();
    const options = document.querySelectorAll('#company-list option');
    const hiddenId = document.getElementById('selected-company-id');
    const packageInput = document.getElementById('package-search-input');
    const specialtySelect = document.getElementById('specialty-select');
    const hiddenPackageId = document.getElementById('selected-package-id');

    let matchedId = null;
    let matchedName = '';

    options.forEach(opt => {
        const text = opt.value.toLowerCase();
        if (text === filter) {
            matchedId = opt.dataset.id;
            matchedName = opt.value;
        }
    });

    if (matchedId) {
        hiddenId.value = matchedId;
        input.value = matchedName;
        
        if (specialtySelect) specialtySelect.disabled = false;
        if (packageInput) packageInput.disabled = false;
        
        document.getElementById('search-form').submit();
    } else {
        hiddenId.value = '';
        
        if (specialtySelect) {
            specialtySelect.disabled = true;
            specialtySelect.value = '';
        }
        if (packageInput) {
            packageInput.disabled = true;
            packageInput.value = '';
        }
        if (hiddenPackageId) hiddenPackageId.value = '';
    }
}

// ============================================================
// ✅ معالجة بحث الباكدج
// ============================================================
function handlePackageSearch(input) {
    const filter = input.value.toLowerCase().trim();
    const options = document.querySelectorAll('#package-list option');
    const hiddenId = document.getElementById('selected-package-id');

    let matchedId = null;
    let matchedName = '';

    options.forEach(opt => {
        const text = opt.value.toLowerCase();
        if (text === filter) {
            matchedId = opt.dataset.id;
            matchedName = opt.value;
        }
    });

    if (matchedId) {
        hiddenId.value = matchedId;
        input.value = matchedName;
        document.getElementById('search-form').submit();
    } else {
        hiddenId.value = '';
    }
}

// ============================================================
// ✅ Enter يروح للبحث
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    const companyInput = document.getElementById('company-search-input');
    const packageInput = document.getElementById('package-search-input');

    [companyInput, packageInput].forEach(input => {
        if (!input) return;
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (input.id === 'company-search-input') {
                    handleCompanySearch(input);
                } else {
                    handlePackageSearch(input);
                }
            }
        });
    });
});
</script>

<!-- ============================================ -->
<!-- ✅ Script تخفيض السعر ومعالجة الملاحظات -->
<!-- ============================================ -->
{% if selected_package %}
<script>
function formatMoney(value) {
    if (value % 1 === 0) {
        return Number(value).toLocaleString("en-US") + " ج.م";
    }
    return Number(value).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + " ج.م";
}

function calculateSuggestedPrice(basePrice, discount) {
    return basePrice * (1 - discount / 100);
}

function calculateSavings(currentPrice, suggestedPrice) {
    return currentPrice - suggestedPrice;
}

function updateSuggestedPrice(currentPrice, suggestedPrice) {
    const input = document.getElementById("suggested-price-display");
    input.textContent = formatMoney(suggestedPrice);
    if (suggestedPrice < currentPrice) {
        input.className = "value text-success";
    }
    else if (suggestedPrice > currentPrice) {
        input.className = "value text-danger";
    }
    else {
        input.className = "value";
    }
}

function updateSavings(savings) {
    const input = document.getElementById("savings-display");
    if (savings > 0) {
        input.textContent = formatMoney(savings);
        input.className = "value text-success";
    }
    else if (savings < 0) {
        input.textContent = formatMoney(Math.abs(savings)) + " (زيادة)";
        input.className = "value text-danger";
    }
    else {
        input.textContent = formatMoney(0);
        input.className = "value";
    }
}

function updatePricingPreview() {
    const basePrice = parseFloat(document.getElementById("base-price").value || 0);
    const currentPrice = parseFloat(document.getElementById("current-price-value").value || 0);
    const discount = parseFloat(document.getElementById("discount-select").value || 0);
    const suggestedPrice = calculateSuggestedPrice(basePrice, discount);
    const savings = calculateSavings(currentPrice, suggestedPrice);
    updateSuggestedPrice(currentPrice, suggestedPrice);
    updateSavings(savings);
}

function updateComparisonTable() {
    const basePrice = parseFloat(document.getElementById("base-price").value || 0);
    const currentPrice = parseFloat(document.getElementById("current-price-value").value || 0);

    [5, 10, 15, 20, 25].forEach(function(discount) {
        const suggestedPrice = calculateSuggestedPrice(basePrice, discount);
        const saving = calculateSavings(currentPrice, suggestedPrice);

        const priceEl = document.getElementById("price" + discount);
        if (priceEl) {
            priceEl.textContent = formatMoney(suggestedPrice);
            priceEl.style.fontWeight = '600';
        }

        const savingEl = document.getElementById("saving" + discount);
        if (savingEl) {
            savingEl.textContent = formatMoney(saving);
            savingEl.style.color = saving >= 0 ? '#198754' : '#dc3545';
            savingEl.style.fontWeight = '600';
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    // ===== تحديث الأسعار =====
    updatePricingPreview();
    updateComparisonTable();
    document.getElementById("discount-select").addEventListener("change", function() {
        updatePricingPreview();
        updateComparisonTable();
    });
    
    // ===== معالجة الملاحظات =====
    const notesDiv = document.getElementById('package-notes');
    if (notesDiv) {
        let htmlContent = notesDiv.innerHTML;
        let tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        let text = tempDiv.textContent.trim();
        
        if (text && text !== 'لا توجد ملاحظات') {
            // تقسيم على * أو - أو \n
            let lines = text.split(/[\*\-\n]+/);
            let cleanLines = [];
            let seen = new Set();
            
            lines.forEach(line => {
                line = line.trim();
                if (!line) return;
                
                line = line.replace(/^["']+|["']+$/g, '');
                line = line.replace(/^[\*\-\s]+/, '');
                line = line.replace(/^الباكدج\s+/, '');
                
                let key = line.toLowerCase().trim();
                if (seen.has(key)) return;
                seen.add(key);
                cleanLines.push(line);
            });
            
            if (cleanLines.length === 1) {
                notesDiv.innerHTML = `<span style="line-height: 1.8;">${cleanLines[0]}</span>`;
            } else if (cleanLines.length > 0) {
                notesDiv.innerHTML = '';
                cleanLines.forEach(line => {
                    const div = document.createElement('div');
                    div.style.cssText = 'display: flex; align-items: flex-start; gap: 10px; padding: 6px 10px; margin-bottom: 6px; background: #f8f9fa; border-radius: 8px; border-right: 3px solid #0d6efd;';
                    
                    const bullet = document.createElement('span');
                    bullet.textContent = '•';
                    bullet.style.cssText = 'color: #0d6efd; font-weight: 700; min-width: 20px;';
                    
                    const textSpan = document.createElement('span');
                    textSpan.textContent = line;
                    textSpan.style.cssText = 'flex: 1; word-wrap: break-word; line-height: 1.6;';
                    
                    div.appendChild(bullet);
                    div.appendChild(textSpan);
                    notesDiv.appendChild(div);
                });
            }
        }
    }
});
</script>
{% endif %}

{% endblock %}