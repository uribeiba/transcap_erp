# config/edp/templatetags/edp_extras.py
from django import template

register = template.Library()

@register.filter
def split(value, key):
    """Split a string by the given key"""
    return value.split(key)