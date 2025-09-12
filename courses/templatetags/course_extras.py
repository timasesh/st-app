from django import template
from django.template.defaultfilters import stringfilter
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key."""
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)

@register.filter
def intersection(queryset1, queryset2):
    return set(queryset1) & set(queryset2)

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def embed_url(url):
    if not url:
        return ''
    
    # YouTube URL patterns
    youtube_regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    youtube_match = re.match(youtube_regex, url)
    
    if youtube_match:
        video_id = youtube_match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
    
    # Vimeo URL pattern
    vimeo_regex = r'vimeo\.com\/([0-9]+)'
    vimeo_match = re.match(vimeo_regex, url)
    
    if vimeo_match:
        video_id = vimeo_match.group(1)
        return f'https://player.vimeo.com/video/{video_id}'
    
    return url

@register.filter
def dict_get(d, key):
    return d.get(key) 