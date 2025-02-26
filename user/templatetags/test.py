from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr)

@register.filter
def keyvalue(dict, key):
    """Возвращает значение по ключу из словаря."""
    return dict.get(key)