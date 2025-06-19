from django import template
from django.urls import reverse
import json

register = template.Library()

@register.filter
def jsonify_slide_urls(slides_queryset):
    """
    Converts a queryset of LessonSlide objects into a JSON array of their image URLs.
    """
    slide_urls = []
    for slide in slides_queryset.all():
        if slide.image:
            slide_urls.append(slide.image.url)
    return json.dumps(slide_urls) 