from django import template
import re

register = template.Library()

@register.filter
def split_notes(value):
    """
    تقسيم الملاحظات وإزالة التكرارات
    """
    if not value:
        return []
    
    # تنظيف النص من علامات التنصيص الزائدة
    value = value.strip('"').strip("'")
    
    # تقسيم على فواصل الأسطر أولاً
    parts = re.split(r'\n+', value)
    
    # تنظيف كل جزء
    cleaned_parts = []
    seen = set()
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # إزالة علامات التنصيص من البداية والنهاية
        part = part.strip('"').strip("'")
        
        # إزالة الأرقام والرموز الزائدة من البداية (مثل "1." أو "*")
        part = re.sub(r'^[\*\d]+\.?\s*', '', part)
        
        # تجاهل التكرارات (نفس النص)
        normalized = part.lower().strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        
        # إذا كان النص يحتوي على "/" أو "&" يمكن تقسيمه أكثر
        if '/' in part and len(part) < 100:
            sub_parts = [p.strip() for p in part.split('/') if p.strip()]
            for sub in sub_parts:
                sub = sub.strip()
                if sub and sub.lower() not in seen:
                    seen.add(sub.lower())
                    cleaned_parts.append(sub)
        else:
            cleaned_parts.append(part)
    
    # إزالة أي تكرارات متبقية
    final_parts = []
    seen_final = set()
    for p in cleaned_parts:
        p_lower = p.lower().strip()
        if p_lower not in seen_final:
            seen_final.add(p_lower)
            final_parts.append(p)
    
    return final_parts

@register.filter
def trim_note(value):
    """
    تنظيف الملاحظة الفردية
    """
    if not value:
        return ""
    
    # إزالة علامات التنصيص
    value = value.strip('"').strip("'")
    
    # إزالة الرموز الزائدة من البداية
    value = re.sub(r'^[\*\d]+\.?\s*', '', value)
    
    # إزالة "الباكدج" المكررة
    value = re.sub(r'^الباكدج\s+', '', value, flags=re.IGNORECASE)
    
    return value.strip()

# ✅ ✅ ✅ فلتر جديد: replace
@register.filter
def replace(value, arg):
    """
    استبدال نص بآخر في السلسلة النصية
    الاستخدام: {{ value|replace:"old:new" }}
    مثال: {{ "hello world"|replace:"world:everyone" }} → "hello everyone"
    """
    if not value or not arg:
        return value
    
    try:
        # arg format: "old:new"
        parts = arg.split(':')
        if len(parts) == 2:
            old, new = parts
            return value.replace(old, new)
        return value
    except Exception:
        return value

# ✅ ✅ ✅ فلتر جديد: split_by_star
@register.filter
def split_by_star(value):
    """
    تقسيم النص على علامة * وإرجاع قائمة
    الاستخدام: {{ value|split_by_star }}
    """
    if not value:
        return []
    
    parts = value.split('*')
    cleaned_parts = []
    for part in parts:
        part = part.strip()
        if part:
            cleaned_parts.append('* ' + part)
    return cleaned_parts