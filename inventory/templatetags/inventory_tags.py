from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def action_badge_color(action_type):
    """Return the appropriate Bootstrap color class based on action type"""
    color_map = {
        'sale': 'success',
        'purchase': 'primary',
        'stock_add': 'info',
        'stock_update': 'info',
        'medicine_add': 'purple',
        'medicine_edit': 'purple',
        'medicine_delete': 'danger',
        'shop_add': 'warning',
        'shop_edit': 'warning',
        'shop_delete': 'danger',
        'alert_resolved': 'warning',
        'other': 'secondary',
    }
    return color_map.get(action_type, 'secondary')

@register.filter
@stringfilter
def replace(value, arg):
    """Replace all instances of arg with space in the given value"""
    return value.replace(arg, " ")

@register.filter
@stringfilter
def underscore_to_space(value):
    """Replace all underscores with spaces in the given value"""
    return value.replace("_", " ") 