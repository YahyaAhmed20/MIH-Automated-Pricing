
celery -A project worker --loglevel=info --concurrency=1 --pool=prefork --time-limit=7200 --soft-time-limit=6000 --queues=local
from imports.services.progress_service import ProgressService

ProgressService.reset()
ProgressService.get()






______________________________


فواتير مماثله 

اجل لغايت متعملها باسم العمود 
ف البحث مش مرتبط مع الفلاتر الفلاتر شغاله مع بعض كويس بس لما بدخل السيرش معاهم مش بيشتغل 


ف الاجاء بيفتح صفحه فيها تفاصيل عايز ازود ع البيانات الي جوه ف بيانات المريض
 اسحب الشركه الفرعيه ف عمود x
 تمام الدكتور ضاف همود جديد اسمه توصيف العمليه سجله + خليه يتسحب ف الصفحه عند  بيانات العملية

______________________________
ف متابعه الباكدجات ف احصائيات الباكدجات شيل لوحه التحكم وحط  متابعه الباكدجات 


  


تاجيل
+ هتلاقي سيرش باسم الباكدج ضيف معاها اني اعمل سيرش بالكود  يعني هيبقي ف ارتباط بين اسم الباكدج والكود يعني لو اسم الباكدج مراره لازم تظهرلي معاه ف السيرش الكود بتاعي واسرش برحتي ي بالاسم او بالكود 

ف  السجلات التفصيلية  عندك المبلغ المفروض يسحب من عمود m سعر الخدمه شيت 11 
__________________________
شيت 6 ,10,11,12,15
دول خليهم يقرا الاهمده اسم فقط عشان لو نقلت العمود من مكان لمكان ميحصلش ايرور 
_____________________________


______________________________________




<datalist>
SEARCH
🚀 تعديل HTML - شيل oninput وخلي الفلترة عند اختيار من datalist

Responsive

Counter Animation

UI Polish

احصائيات الموافقات 

شبه تحليل الحالات pending  
فهمني خليها عصاره كل المشروع

/ متابعة موافقات الخارجي شيت ١٢ 10


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


old report
{% extends 'frontend/base.html' %}
{% load static %}

{% block content %}

<style>
    /* ============================================ */
    /* ✅ Stats Cards - ثلاث بوكسات */
    /* ============================================ */
    .stats-card {
        border-radius: 16px;
        padding: 1.5rem 1.25rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: none;
        color: #fff;
        position: relative;
        overflow: hidden;
        cursor: default;
    }
    
    .stats-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
    }
    
    .stats-card .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.2;
    }
    
    .stats-card .stats-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-top: 6px;
    }
    
    .stats-card .stats-icon {
        font-size: 2rem;
        opacity: 0.2;
        position: absolute;
        bottom: 10px;
        right: 15px;
    }
    
    .stats-card-total {
        background: linear-gradient(135deg, #1a237e, #0d47a1);
    }
    
    .stats-card-credit {
        background: linear-gradient(135deg, #e65100, #f57c00);
    }
    
    .stats-card-cash {
        background: linear-gradient(135deg, #2e7d32, #43a047);
    }
    
    /* ============================================ */
    /* ✅ Payment Chart */
    /* ============================================ */
    .payment-chart-wrapper {
        width: 340px;
        height: 340px;
        margin: auto;
        position: relative;
    }
    
    @media (max-width: 992px) {
        .payment-chart-wrapper {
            width: 280px;
            height: 280px;
        }
    }
    
    /* ============================================ */
    /* ✅ Specialty Cards - محسّن */
    /* ============================================ */
    .specialty-card {
        border-radius: 20px;
        border: 1px solid #e9ecef;
        overflow: hidden;
        background: #fff;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        width: 100%;
    }
    
    .specialty-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.1);
    }
    
    .specialty-card .specialty-header {
        padding: 1.25rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
        border-bottom: 2px solid #f1f3f5;
        flex-wrap: wrap;
    }
    
    .specialty-card .specialty-icon-wrapper {
        width: 72px;
        height: 72px;
        min-width: 72px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.4rem;
        color: #fff;
        flex-shrink: 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        position: relative;
    }
    
    .specialty-card:hover .specialty-icon-wrapper {
        transform: scale(1.08) rotate(-6deg);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
    .specialty-card .specialty-icon-wrapper::after {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        border: 2px solid currentColor;
        opacity: 0;
        transition: all 0.4s ease;
    }
    
    .specialty-card:hover .specialty-icon-wrapper::after {
        opacity: 0.3;
        transform: scale(1.05);
    }
    
    .specialty-card .specialty-info {
        flex: 1;
        min-width: 0;
    }
    
    .specialty-card .specialty-name {
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.3;
    }
    
    .specialty-card .specialty-stats {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-top: 4px;
    }
    
    .specialty-card .specialty-stats span {
        font-size: 0.75rem;
        color: #6c757d;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    
    .specialty-card .specialty-stats .stat-total {
        color: #0d6efd;
        font-weight: 600;
    }
    
    .specialty-card .specialty-stats .stat-cash {
        color: #2e7d32;
        font-weight: 600;
    }
    
    .specialty-card .specialty-stats .stat-credit {
        color: #e65100;
        font-weight: 600;
    }
    
    /* ============================================ */
    /* ✅ Sticky Filter */
    /* ============================================ */
    .filter-sticky {
        position: sticky;
        top: 10px;
        z-index: 1050;
        background: rgba(255,255,255,.96);
        backdrop-filter: blur(10px);
        border-radius: 18px;
        transition: all .3s ease;
    }
    
    .filter-sticky.stuck{
        box-shadow: 0 10px 30px rgba(0,0,0,.12);
    }
    
    /* ✅ Months Scroll - أفقي */
    .months-scroll {
        display: flex;
        overflow-x: auto;
        gap: 10px;
        padding: 8px 0 12px 0;
        scrollbar-width: none;
        -webkit-overflow-scrolling: touch;
    }
    
    .months-scroll::-webkit-scrollbar {
        display: none;
    }
    
    .month-pill {
        white-space: nowrap;
        text-decoration: none;
        padding: 8px 20px;
        border-radius: 30px;
        background: #f4f6f9;
        color: #444;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.25s ease;
        border: 2px solid transparent;
        flex-shrink: 0;
        cursor: pointer;
    }
    
    .month-pill:hover {
        background: #0d6efd;
        color: white;
        transform: scale(1.05);
        text-decoration: none;
    }
    
    .month-pill.active {
        background: #0d6efd;
        color: white;
        border-color: #0d6efd;
        box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
    }
    
    .month-pill.all-pill {
        background: #6c757d;
        color: white;
    }
    
    .month-pill.all-pill:hover {
        background: #5a6268;
    }
    
    .month-pill.all-pill.active {
        background: #0d6efd;
        border-color: #0d6efd;
    }
    
    /* ✅ Chart Placeholder */
    .chart-placeholder {
        height: 100px;
        position: relative;
    }
    
    .chart-placeholder canvas {
        width: 100% !important;
        height: 100% !important;
    }
    
    /* ✅ Responsive */
    @media (max-width: 768px) {
        .stats-card .stats-number {
            font-size: 1.8rem;
        }
        
        .specialty-card .specialty-header {
            flex-direction: column;
            text-align: center;
        }
        
        .specialty-card .specialty-icon-wrapper {
            width: 56px;
            height: 56px;
            min-width: 56px;
            font-size: 1.8rem;
        }
        
        .specialty-card .specialty-stats {
            justify-content: center;
        }
        
        .month-pill {
            padding: 6px 14px;
            font-size: 0.75rem;
        }
        
        .months-scroll {
            gap: 6px;
        }
    }
</style>

<!-- ============================================ -->
<!-- ✅ العنوان -->
<!-- ============================================ -->
<div class="container-fluid py-4">
    
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="mb-0 fw-bold">
                <i class="fas fa-chart-bar text-primary me-2"></i>
                التقارير والإحصائيات
            </h4>
            <p class="text-muted small mb-0">حركة الباكجات الطبية</p>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ فلتر الشهور (Sticky) -->
    <!-- ============================================ -->
    <div class="card shadow-sm mb-4 border-0 filter-sticky">
        <div class="card-body">
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-calendar-alt text-primary me-2"></i>
                <h6 class="mb-0 fw-bold">حركة الباكجات</h6>
            </div>
            <div class="months-scroll">
                <a href="?" class="month-pill all-pill {% if not selected_month %}active{% endif %}">
                    <i class="fas fa-undo me-1"></i> الكل
                </a>
                {% for month in months %}
                <a href="?month={{ month }}" class="month-pill {% if month == selected_month %}active{% endif %}">
                    {{ month }}
                </a>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ ثلاث بوكسات مع كاونتر -->
    <!-- ============================================ -->
    <div class="row g-4 mb-4">
        
        <div class="col-md-4">
            <div class="stats-card stats-card-total">
                <div class="stats-number counter" data-target="{{ total_packages }}">0</div>
                <div class="stats-label"><i class="fas fa-boxes me-1"></i>إجمالي الباكدجات</div>
                <div class="stats-icon"><i class="fas fa-boxes"></i></div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="stats-card stats-card-cash">
                <div class="stats-number counter" data-target="{{ cash_packages }}">0</div>
                <div class="stats-label"><i class="fas fa-money-bill-wave me-1"></i>باكدجات النقدي</div>
                <div class="stats-icon"><i class="fas fa-money-bill-wave"></i></div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="stats-card stats-card-credit">
                <div class="stats-number counter" data-target="{{ credit_packages }}">0</div>
                <div class="stats-label"><i class="fas fa-clock me-1"></i>باكدجات الآجل</div>
                <div class="stats-icon"><i class="fas fa-clock"></i></div>
            </div>
        </div>
        
    </div>

   <!-- ============================================ -->
<!-- ✅ التخصصات - محسّن -->
<!-- ============================================ -->
<div class="row g-4">
    {% for specialty in specialties %}
    
    <div class="col-xl-4 col-lg-6">
        <div class="card specialty-card h-100">
            
            <div class="specialty-header">
                <div class="specialty-icon-wrapper" style="background: {{ specialty.color }};">
                    <i class="{{ specialty.icon }}"></i>
                </div>
                <div class="specialty-info">
                    <h5 class="specialty-name" style="color: {{ specialty.color }};">
                        {{ specialty.name }}
                    </h5>
                    <div class="specialty-stats">
                       
                    </div>
                </div>
            </div>
                
                <div class="card-body">
                    
                    <!-- ✅ الرسم البياني -->
                    <div class="chart-placeholder mb-3">
                        <canvas id="chart{{ forloop.counter }}"></canvas>
                    </div>
                    
                    <!-- ✅ إجمالي الباكجات (كاونتر متحرك) -->
                    <div class="text-center mb-3">
                        <div class="display-5 fw-bold text-primary counter" data-target="{{ specialty.total }}">
                            0
                        </div>
                        <small class="text-muted">إجمالي الباكجات</small>
                    </div>
                    
                    <div class="row g-2">
                        <!-- ✅ باكجات نقدي -->
                        <div class="col-6">
                            <div class="card bg-success bg-opacity-10 border-0 h-100">
                                <div class="card-body py-3 text-center">
                                    <div class="fw-bold text-success">💰 نقدي</div>
                                    <div class="fs-3 fw-bold">{{ specialty.cash }}</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- ✅ باكجات آجل -->
                        <div class="col-6">
                            <div class="card bg-warning bg-opacity-10 border-0 h-100">
                                <div class="card-body py-3 text-center">
                                    <div class="fw-bold text-warning">📄 آجل</div>
                                    <div class="fs-3 fw-bold">{{ specialty.credit }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- ✅ زر عرض المزيد -->
                    <div class="mt-3">
                        <a href="{% url 'specialty_detail' specialty.name %}?month={{ selected_month }}" 
                           class="btn btn-outline-primary btn-sm w-100">
                            <i class="fas fa-eye me-1"></i> عرض المزيد
                            <span class="badge bg-secondary ms-1">{{ specialty.records|length }}</span>
                        </a>
                    </div>
                    
                </div>
            </div>
        </div>
        
        {% empty %}
        
        <div class="col-12">
            <div class="alert alert-info text-center py-5">
                <i class="fas fa-inbox fa-3x d-block mb-3 text-muted"></i>
                <h5>لا توجد بيانات</h5>
                <p class="text-muted small">لا توجد سجلات في قاعدة البيانات</p>
            </div>
        </div>
        
        {% endfor %}
    </div>

    <!-- ============================================ -->
    <!-- ✅ الباكجات حسب نوع الدفع (Doughnut Chart) -->
    <!-- ============================================ -->
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="fw-bold mb-1">
                        <i class="fas fa-chart-pie text-primary me-2"></i>
                        الباكجات حسب نوع الدفع
                    </h5>
                    <small class="text-muted">إجمالي الباكجات حسب طريقة الدفع</small>
                </div>
                <!-- ✅ زر عرض المزيد -->
                <a href="{% url 'payment_details' %}" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-eye me-1"></i>
                    عرض المزيد
                    <span class="badge bg-secondary ms-1">{{ total_packages }}</span>
                </a>
            </div>
        </div>
        <div class="card-body">
            <div class="row align-items-center">
                <div class="col-lg-6 text-center">
                    <div class="payment-chart-wrapper">
                        <canvas id="paymentChart"></canvas>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="card border-0 bg-success bg-opacity-10 mb-3">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="fw-bold text-success mb-1">{{ cash_packages }}</h5>
                                    <small class="text-muted">باكدج نقدي</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-success rounded-pill fs-6">{{ cash_percentage }}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card border-0 bg-warning bg-opacity-10">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="fw-bold text-warning mb-1">{{ credit_packages }}</h5>
                                    <small class="text-muted">باكدج آجل</small>
                                </div>
                                <div class="text-end">
                                    <span class="badge bg-warning text-dark rounded-pill fs-6">{{ credit_percentage }}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ الباكجات حسب القطاع (آجل فقط) - معدل -->
    <!-- ============================================ -->
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-white border-0 py-3">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="fw-bold mb-1">
                        <i class="fas fa-chart-pie text-primary me-2"></i>
                        الباكجات حسب القطاع (آجل فقط)
                    </h5>
                    <small class="text-muted">توزيع الباكجات الآجلة حسب القطاع</small>
                </div>
                <!-- ✅ زر عرض المزيد -->
                <a href="{% url 'sector_details' %}" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-eye me-1"></i>
                    عرض المزيد
                    <span class="badge bg-secondary ms-1">{{ credit_packages }}</span>
                </a>
            </div>
        </div>
        <div class="card-body">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <div class="payment-chart-wrapper">
                        <canvas id="sectorChart"></canvas>
                    </div>
                </div>
                <div class="col-lg-6">
                    {% for sector in sector_data %}
                    <div class="card border-0 mb-2" style="background: {{ sector.color }}20; border-left: 4px solid {{ sector.color }};">
                        <div class="card-body py-2">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="d-flex align-items-center gap-2">
                                        <span class="badge" style="background: {{ sector.color }}; width: 12px; height: 12px; border-radius: 50%; padding: 0;"></span>
                                        <strong style="color: {{ sector.color }};">{{ sector.name }}</strong>
                                    </div>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold" style="color: {{ sector.color }};">{{ sector.total }}</div>
                                    <small class="text-muted">{{ sector.percentage }}%</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="text-center py-4">
                        <i class="fas fa-inbox fa-2x text-muted mb-2 d-block"></i>
                        <p class="text-muted mb-0">لا توجد بيانات للقطاعات</p>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- ============================================ -->
    <!-- ✅ أعلى وأقل 5 جهات (آجل فقط) -->
    <!-- ============================================ -->
    <div class="row g-4 mb-4">

        <!-- أعلى 5 جهات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold mb-0">🏆 أعلى 5 جهات (آجل)</h5>
                        <a href="{% url 'entities_details' %}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-eye me-1"></i>
                            عرض المزيد
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    {% for entity in top_entities %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <div>
                                {% if forloop.counter == 1 %}🥇
                                {% elif forloop.counter == 2 %}🥈
                                {% elif forloop.counter == 3 %}🥉
                                {% else %}{{ forloop.counter }}.{% endif %}
                                <strong>{{ entity.name }}</strong>
                            </div>
                            <span class="badge bg-success counter" data-target="{{ entity.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-success" style="width: {{ entity.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ entity.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- أقل 5 جهات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold mb-0">📉 أقل 5 جهات (آجل)</h5>
                        <a href="{% url 'entities_details' %}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-eye me-1"></i>
                            عرض المزيد
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    {% for entity in bottom_entities %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong>{{ entity.name }}</strong>
                            <span class="badge bg-danger counter" data-target="{{ entity.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-danger" style="width: {{ entity.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ entity.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>

    <!-- ============================================ -->
    <!-- ✅ أعلى وأقل 5 شركات فرعية (آجل فقط) -->
    <!-- ============================================ -->
    <div class="row g-4 mb-4">

        <!-- أعلى 5 شركات فرعية -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold mb-0">🏢 أعلى 5 شركات فرعية (آجل)</h5>
                        <a href="{% url 'sub_companies_details' %}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-eye me-1"></i>
                            عرض المزيد
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    {% for company in top_sub_companies %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <div>
                                {% if forloop.counter == 1 %}🥇
                                {% elif forloop.counter == 2 %}🥈
                                {% elif forloop.counter == 3 %}🥉
                                {% else %}{{ forloop.counter }}.{% endif %}
                                <strong>{{ company.name }}</strong>
                            </div>
                            <span class="badge bg-success counter" data-target="{{ company.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-success" style="width: {{ company.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ company.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- أقل 5 شركات فرعية -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold mb-0">📉 أقل 5 شركات فرعية (آجل)</h5>
                        <a href="{% url 'sub_companies_details' %}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-eye me-1"></i>
                            عرض المزيد
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    {% for company in bottom_sub_companies %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong>{{ company.name }}</strong>
                            <span class="badge bg-danger counter" data-target="{{ company.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-danger" style="width: {{ company.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ company.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>

    <!-- ============================================ -->
    <!-- ✅ أعلى وأقل 5 تخصصات -->
    <!-- ============================================ -->
    <div class="row g-4 mb-4">

        <!-- أعلى 5 تخصصات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <h5 class="fw-bold mb-0">🩺 أعلى 5 تخصصات</h5>
                </div>
                <div class="card-body">
                    {% for specialty in top_specialties %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <div>
                                {% if forloop.counter == 1 %}🥇
                                {% elif forloop.counter == 2 %}🥈
                                {% elif forloop.counter == 3 %}🥉
                                {% else %}{{ forloop.counter }}.{% endif %}
                                <strong>{{ specialty.name }}</strong>
                            </div>
                            <span class="badge bg-success counter" data-target="{{ specialty.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-success" style="width: {{ specialty.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ specialty.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- أقل 5 تخصصات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <h5 class="fw-bold mb-0">📉 أقل 5 تخصصات</h5>
                </div>
                <div class="card-body">
                    {% for specialty in bottom_specialties %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong>{{ specialty.name }}</strong>
                            <span class="badge bg-danger counter" data-target="{{ specialty.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-danger" style="width: {{ specialty.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ specialty.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>

    <!-- ============================================ -->
    <!-- ✅ أعلى وأقل 5 باكدجات -->
    <!-- ============================================ -->
    <div class="row g-4 mb-4">

        <!-- أعلى 5 باكدجات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <h5 class="fw-bold mb-0">📦 أعلى 5 باكدجات</h5>
                </div>
                <div class="card-body">
                    {% for package in top_packages %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <div>
                                {% if forloop.counter == 1 %}🥇
                                {% elif forloop.counter == 2 %}🥈
                                {% elif forloop.counter == 3 %}🥉
                                {% else %}{{ forloop.counter }}.{% endif %}
                                <strong>{{ package.name }}</strong>
                            </div>
                            <span class="badge bg-success counter" data-target="{{ package.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-success" style="width: {{ package.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ package.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- أقل 5 باكدجات -->
        <div class="col-lg-6">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white">
                    <h5 class="fw-bold mb-0">📉 أقل 5 باكدجات</h5>
                </div>
                <div class="card-body">
                    {% for package in bottom_packages %}
                    <div class="mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong>{{ package.name }}</strong>
                            <span class="badge bg-danger counter" data-target="{{ package.percentage }}">0%</span>
                        </div>
                        <div class="progress mb-2" style="height:8px;">
                            <div class="progress-bar bg-danger" style="width: {{ package.percentage }}%;"></div>
                        </div>
                        <small class="text-muted counter" data-target="{{ package.total }}">0</small>
                    </div>
                    {% empty %}
                    <div class="text-center text-muted">لا توجد بيانات</div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>
</div>
<!-- ====== نهاية container-fluid ====== -->

<!-- ============================================ -->
<!-- ✅ Chart.js -->
<!-- ============================================ -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // ✅ 1. الكاونترات المتحركة - لكل الأرقام
    // ============================================
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        let current = 0;
        const increment = Math.max(1, Math.ceil(target / 50));
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                if (current > target) current = target;
                counter.textContent = current;
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
    
    // ============================================
    // ✅ 2. Function to create Doughnut Chart
    // ============================================
    function createDoughnutChart(canvasId, labels, values, colors, centerTitle, centerValue) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const centerTextPlugin = {
            id: "centerText",
            beforeDraw(chart) {
                const {ctx} = chart;
                const meta = chart.getDatasetMeta(0);
                if (!meta.data.length) return;
                const x = meta.data[0].x;
                const y = meta.data[0].y;
                ctx.save();
                ctx.textAlign = "center";
                ctx.fillStyle = "#6c757d";
                ctx.font = "18px Cairo";
                ctx.fillText(centerTitle, x, y - 18);
                ctx.fillStyle = "#212529";
                ctx.font = "bold 42px Cairo";
                ctx.fillText(centerValue, x, y + 12);
                ctx.fillStyle = "#6c757d";
                ctx.font = "16px Cairo";
                ctx.fillText("باكدج", x, y + 38);
                ctx.restore();
            }
        };
        
        new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: "#ffffff",
                    borderWidth: 4,
                    hoverOffset: 20,
                    hoverBorderWidth: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: "68%",
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1800,
                    easing: "easeOutQuart"
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return context.label + ": " + value + " (" + percent + "%)";
                            }
                        }
                    }
                }
            },
            plugins: [centerTextPlugin]
        });
    }
    
    // ============================================
    // ✅ 3. Payment Type Doughnut Chart
    // ============================================
    createDoughnutChart(
        "paymentChart",
        ["نقدي", "آجل"],
        [{{ cash_packages }}, {{ credit_packages }}],
        ["#2e7d32", "#1976d2"],
        "الإجمالي",
        "{{ total_packages }}"
    );
    
    // ============================================
    // ✅ 4. Sector Doughnut Chart
    // ============================================
    const sectorLabels = {{ sector_labels|safe }};
    const sectorValues = {{ sector_values|safe }};
    const sectorColors = {{ sector_colors|safe }};
    
    if (sectorLabels.length > 0) {
        createDoughnutChart(
            "sectorChart",
            sectorLabels,
            sectorValues,
            sectorColors.slice(0, sectorLabels.length),
            "إجمالي الآجل",
            "{{ credit_packages }}"
        );
    }
    
    // ============================================
    // ✅ 5. الرسوم البيانية - Line Charts للتخصصات
    // ============================================
    {% for specialty in specialties %}
    const ctx{{ forloop.counter }} = document.getElementById("chart{{ forloop.counter }}");
    if (ctx{{ forloop.counter }}) {
        new Chart(ctx{{ forloop.counter }}, {
            type: "line",
            data: {
                labels: {{ specialty.chart_labels|safe }},
                datasets: [{
                    label: "{{ specialty.name }}",
                    data: {{ specialty.chart_values|safe }},
                    borderColor: "{{ specialty.color }}",
                    backgroundColor: "{{ specialty.color }}20",
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: "{{ specialty.color }}",
                    pointBorderColor: "#fff",
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context){
                                return context.parsed.y + " باكج";
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: "index"
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, precision: 0 },
                        grid: { color: "#f1f3f5" }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    {% endfor %}
    
    // ============================================
    // ✅ 6. Sticky Filter Shadow
    // ============================================
    const stickyFilter = document.querySelector(".filter-sticky");
    window.addEventListener("scroll", function () {
        if (window.scrollY > 40) {
            stickyFilter.classList.add("stuck");
        } else {
            stickyFilter.classList.remove("stuck");
        }
    });
    
});
</script>

{% endblock %}