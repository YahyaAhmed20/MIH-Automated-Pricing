from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def format_number(value):
    try:
        # تحويل الرقم لـ float وتنسيقه
        num = float(value)
        formatted = f"{num:,.2f}"  # فواصل الآلاف ومنزلتين عشريتين
        return formatted
    except:
        return value