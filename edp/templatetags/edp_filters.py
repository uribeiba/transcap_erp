from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attribute):
    """Suma los valores de un atributo en un queryset"""
    total = 0
    for obj in queryset:
        value = getattr(obj, attribute, 0)
        try:
            total += float(value)
        except (TypeError, ValueError):
            pass
    return total

@register.filter
def negative(value):
    """Convierte un número a negativo (para mostrar saldo pendiente)"""
    try:
        return -float(value)
    except (TypeError, ValueError):
        return value