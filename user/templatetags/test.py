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

@register.filter
def times(number):
    return range(1, number + 1)

@register.filter
def dict_key(dictionary, key):
    return dictionary.get(key, None)

# @register.filter
# def add(value, arg):
#     return str(value) + str(arg)

# @register.filter
# def widthratio(value, max_value, max_width):
#     try:
#         return (float(value) / float(max_value)) * max_width
#     except (ValueError, ZeroDivisionError):
#         return 0