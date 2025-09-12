from django import template
from django.urls import reverse
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def level_progress(student):
    """
    Template filter to calculate student's progress to next level.
    Usage: {{ student|level_progress }}
    """
    if not student or not student.level:
        return 0
    
    current_stars = student.stars
    current_level = student.level
    
    # Если это последний уровень, прогресс 100%
    next_level = current_level.get_next_level()
    if not next_level:
        return 100
    
    # Рассчитываем прогресс
    stars_needed = next_level.min_stars - current_level.min_stars
    stars_earned = current_stars - current_level.min_stars
    
    if stars_needed <= 0:
        return 100
    
    progress = (stars_earned / stars_needed) * 100
    return min(100, max(0, progress))

@register.filter
def stars_to_next_level(student):
    """
    Template filter to calculate stars needed for next level.
    Usage: {{ student|stars_to_next_level }}
    """
    if not student or not student.level:
        return 0
    
    current_stars = student.stars
    current_level = student.level
    
    # Если это последний уровень, возвращаем 0
    next_level = current_level.get_next_level()
    if not next_level:
        return 0
    
    stars_needed = next_level.min_stars - current_stars
    return max(0, stars_needed)

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