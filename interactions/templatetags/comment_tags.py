import re
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def render_mentions(text):
    """Wraps @username in a colored span."""
    if not text:
        return ""
    # First escape as usual
    escaped_text = escape(text)
    # Then replace @username with span using the platform's primary blue color
    pattern = r'@([\w.-]+)'
    replacement = r'<a href="/users/profile/\1/" class="text-[#1D9BF0] hover:underline cursor-pointer group-hover/mention:underline font-medium">@\1</a>'
    html = re.sub(pattern, replacement, escaped_text)
    # also handle linebreaks
    html = html.replace('\n', '<br>')
    return mark_safe(html)
