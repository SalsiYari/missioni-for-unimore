from django import template

register = template.Library()

@register.filter
def add_data_modified(field, value):
    return field.as_widget(attrs={'data-modified': value})
