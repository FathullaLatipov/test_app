from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    return getattr(obj, attr, '')

@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return ''
    return dictionary.get(key, '')