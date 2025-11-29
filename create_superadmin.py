"""
Скрипт для создания суперпользователя с логином timaadmin и паролем admin2010

Этот скрипт можно запустить двумя способами:
1. Через Django management команду: python manage.py shell < create_superadmin.py
2. Через URL: https://study-task.kz/create_admin
3. Напрямую: python manage.py shell, затем скопировать и выполнить код ниже

Или добавить в manage.py команду (см. create_admin_management_command.py)
"""

import os
import sys
import django

# Настройка Django окружения
if __name__ == '__main__':
    # Добавляем путь к проекту
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Настраиваем Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_courses.settings')
    django.setup()

from courses.models import User

def create_superadmin():
    """Создание или обновление суперпользователя"""
    username = 'timaadmin'
    password = 'admin2010'
    
    # Проверяем, существует ли уже пользователь с таким username
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        # Обновляем пароль и права
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.is_admin = True
        user.save()
        print(f'✅ Пользователь "{username}" уже существует. Пароль обновлен, права суперпользователя установлены.')
    else:
        # Создаем нового суперпользователя
        user = User.objects.create_user(
            username=username,
            password=password,
            is_superuser=True,
            is_staff=True,
            is_active=True,
            is_admin=True
        )
        print(f'✅ Суперпользователь "{username}" успешно создан!')
    
    print(f'\n📋 Данные для входа:')
    print(f'   Логин: {username}')
    print(f'   Пароль: {password}')
    print(f'\n🔗 Ссылки:')
    print(f'   Админ-панель: https://study-task.kz/admin/')
    print(f'   Создание через URL: https://study-task.kz/create_admin')
    
    return user

if __name__ == '__main__':
    create_superadmin()

