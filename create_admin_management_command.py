"""
Альтернативный вариант: Django management команда для создания суперпользователя

Чтобы использовать этот вариант, создайте файл:
courses/management/commands/create_admin.py

Содержимое файла:
"""

COMMAND_CONTENT = """
from django.core.management.base import BaseCommand
from courses.models import User


class Command(BaseCommand):
    help = 'Создает суперпользователя с логином timaadmin и паролем admin2010'

    def handle(self, *args, **options):
        username = 'timaadmin'
        password = 'admin2010'
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.is_admin = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Пользователь "{username}" обновлен. Пароль изменен.')
            )
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                is_superuser=True,
                is_staff=True,
                is_active=True,
                is_admin=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Суперпользователь "{username}" успешно создан!')
            )
        
        self.stdout.write(f'Логин: {username}')
        self.stdout.write(f'Пароль: {password}')
"""

print("Этот файл содержит пример команды для Django management.")
print("Создайте файл courses/management/commands/create_admin.py с содержимым выше.")
print("Затем используйте: python manage.py create_admin")

