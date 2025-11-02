from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Course, Module, Lesson


class StaticViewSitemap(Sitemap):
    """Карта сайта для статических страниц."""
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return [
            'landing_page',
            'student_login',
            'student_registration',
        ]

    def location(self, item):
        return reverse(item)


class CourseSitemap(Sitemap):
    """Карта сайта для курсов."""
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Course.objects.all()

    def location(self, obj):
        return f"/course/{obj.id}/"

    def lastmod(self, obj):
        # Можно добавить поле updated_at в модель Course если нужно
        return None


class ModuleSitemap(Sitemap):
    """Карта сайта для модулей."""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Module.objects.all()

    def location(self, obj):
        return f"/module/details/{obj.id}/"


class LessonSitemap(Sitemap):
    """Карта сайта для уроков."""
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Lesson.objects.all()

    def location(self, obj):
        return f"/lesson/{obj.id}/"

