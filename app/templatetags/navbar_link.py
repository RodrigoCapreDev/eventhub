from django import template
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def navbar_link(context, url_name, label):
    path = reverse(url_name)
    is_active = path in context.request.path

    css_class = "nav-link active" if is_active else "nav-link"
    aria = 'aria-current="page"' if is_active else ""

    html = f"<a href='{path}' class='{css_class}' {aria}>{label}</a>"

    return format_html(html)
