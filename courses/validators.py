from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import re

class VideoURLValidator:
    """Валидатор для проверки URL видео с различных сервисов"""
    
    SUPPORTED_SERVICES = {
        'youtube': {
            'domains': ['youtube.com', 'youtu.be'],
            'patterns': [
                r'youtube\.com/watch\?v=[a-zA-Z0-9_-]+',
                r'youtu\.be/[a-zA-Z0-9_-]+'
            ]
        },
        'vimeo': {
            'domains': ['vimeo.com'],
            'patterns': [
                r'vimeo\.com/\d+'
            ]
        },
        'google_drive': {
            'domains': ['drive.google.com'],
            'patterns': [
                r'drive\.google\.com/file/d/[a-zA-Z0-9_-]+',
                r'drive\.google\.com/open\?id=[a-zA-Z0-9_-]+'
            ]
        },
        'dropbox': {
            'domains': ['dropbox.com'],
            'patterns': [
                r'dropbox\.com/s/[a-zA-Z0-9_-]+/.*\.(mp4|avi|mov|wmv|flv|webm)'
            ]
        },
        'onedrive': {
            'domains': ['1drv.ms', 'onedrive.live.com'],
            'patterns': [
                r'1drv\.ms/v/[a-zA-Z0-9_-]+',
                r'onedrive\.live\.com/.*(redir|embed)'
            ]
        }
    }

    def __init__(self, message=None):
        self.message = message or 'Некорректная ссылка на видео'
        self.url_validator = URLValidator()

    def __call__(self, value):
        if not value:
            return

        # Проверка базового формата URL
        try:
            self.url_validator(value)
        except ValidationError:
            raise ValidationError('Некорректный формат URL')

        # Проверка на соответствие поддерживаемым сервисам
        is_valid = False
        for service, config in self.SUPPORTED_SERVICES.items():
            if any(domain in value.lower() for domain in config['domains']):
                if any(re.search(pattern, value) for pattern in config['patterns']):
                    is_valid = True
                    break

        if not is_valid:
            raise ValidationError(
                'Неподдерживаемый сервис или некорректный формат ссылки. '
                'Используйте YouTube, Vimeo, Google Drive, Dropbox или OneDrive'
            )

def validate_video_url(value):
    """Функция-обертка для удобного использования валидатора"""
    validator = VideoURLValidator()
    validator(value) 