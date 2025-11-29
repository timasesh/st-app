"""
Скрипт для создания преподавателя с указанными данными

Этот скрипт можно запустить двумя способами:
1. Через Django management команду: python manage.py shell < create_teacher.py
2. Через URL: https://study-task.kz/create_teacher
3. Напрямую: python manage.py shell, затем скопировать и выполнить код ниже
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

from courses.models import User, Teacher

def create_teacher():
    """Создание или обновление преподавателя"""
    email = 'teacheer@gmail.com'
    username = email
    password = 'teacher2010'
    first_name = 'Учитель'
    last_name = 'Учитель'
    phone_number = '8777 777 77 77'
    specialization = 'Математика, Физика'
    bio = 'Преподаватель по математике и физике'
    
    try:
        # Проверяем, существует ли уже пользователь с таким email/username
        user_exists = User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists()
        teacher_exists = Teacher.objects.filter(email=email).exists()
        
        if user_exists:
            # Если пользователь существует, обновляем его
            user = User.objects.filter(username=username).first() or User.objects.filter(email=email).first()
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.is_teacher = True
            user.is_active = True
            user.save()
            
            # Обновляем или создаем профиль преподавателя
            teacher, created = Teacher.objects.get_or_create(
                email=email,
                defaults={
                    'user': user,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone_number,
                    'specialization': specialization,
                    'bio': bio,
                }
            )
            
            if not created:
                # Обновляем существующий профиль
                teacher.user = user
                teacher.first_name = first_name
                teacher.last_name = last_name
                teacher.phone_number = phone_number
                teacher.specialization = specialization
                teacher.bio = bio
                teacher.is_active = True
                teacher.save()
            
            print(f'✅ Преподаватель "{first_name} {last_name}" уже существовал. Данные обновлены.')
        else:
            # Создаем нового пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_teacher=True,
                is_active=True
            )
            
            # Создаем профиль преподавателя
            teacher = Teacher.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                specialization=specialization,
                bio=bio,
                is_active=True
            )
            
            print(f'✅ Преподаватель "{first_name} {last_name}" успешно создан!')
        
        print(f'\n📋 Данные для входа:')
        print(f'   Логин: {email}')
        print(f'   Пароль: {password}')
        print(f'\n👤 Информация о преподавателе:')
        print(f'   Имя: {first_name}')
        print(f'   Фамилия: {last_name}')
        print(f'   Email: {email}')
        print(f'   Номер телефона: {phone_number}')
        print(f'   Специализация: {specialization}')
        print(f'   О преподавателе: {bio}')
        print(f'\n🔗 Ссылки:')
        print(f'   Панель преподавателя: https://study-task.kz/teacher_dashboard/')
        print(f'   Создание через URL: https://study-task.kz/create_teacher')
        
        return teacher
        
    except Exception as e:
        print(f'❌ Ошибка при создании преподавателя: {str(e)}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    create_teacher()

