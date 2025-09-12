from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' 

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def level_progress(student):
    """Возвращает процент прогресса в текущем уровне"""
    try:
        level = student.get_level()
        if not level:
            return 0
        
        stars_in_level = student.stars - level.min_stars
        level_range = level.max_stars - level.min_stars
        
        if level_range <= 0:
            return 100
            
        progress = (stars_in_level / level_range) * 100
        return max(0, min(100, progress))
    except:
        return 0

@register.filter
def stars_to_next_level(student):
    """Возвращает количество звезд до следующего уровня"""
    try:
        level = student.get_level()
        if not level:
            return 0
        return max(0, level.max_stars - student.stars)
    except:
        return 0 