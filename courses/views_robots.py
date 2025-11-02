from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    """
    Возвращает robots.txt файл для SEO.
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Блокируем служебные страницы",
        "Disallow: /admin/",
        "Disallow: /teacher/",
        "Disallow: /student_page/",
        "Disallow: /profile/",
        "",
        "Sitemap: https://study-task.kz/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

