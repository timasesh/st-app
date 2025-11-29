# Инструкция по созданию пользователей

## Описание

Система позволяет создавать администратора и преподавателя через специальные URL-эндпоинты или скрипты.

---

## Создание администратора (Суперпользователь)

### Способ 1: Через URL (Рекомендуется) ⭐

**URL:** `https://study-task.kz/create_admin`

**Параметры создаваемого пользователя:**

- **Логин:** `timaadmin`
- **Пароль:** `admin2010`
- **is_superuser:** `True`
- **is_staff:** `True`
- **is_admin:** `True`
- **is_active:** `True`

### Способ 2: Через Python скрипт

```bash
python create_superadmin.py
```

---

## Создание преподавателя

### Способ 1: Через URL (Рекомендуется) ⭐

**URL:** `https://study-task.kz/create_teacher`

**Параметры создаваемого преподавателя:**

- **Логин:** `teacheer@gmail.com`
- **Email:** `teacheer@gmail.com`
- **Пароль:** `teacher2010`
- **Имя:** `Учитель`
- **Фамилия:** `Учитель`
- **Номер телефона:** `8777 777 77 77`
- **Специализация:** `Математика, Физика`
- **О преподавателе:** `Преподаватель по математике и физике`
- **is_teacher:** `True`
- **is_active:** `True`

### Способ 2: Через Python скрипт

```bash
python create_teacher.py
```

---

## Технические детали

### Файлы проекта:

#### Для администратора:

1. **`courses/views.py`** - функция `create_admin()`

   - Создает суперпользователя с логином `timaadmin`
   - Расположение: конец файла

2. **`courses/urls.py`** - URL маршрут

   - `path('create_admin/', views.create_admin, name='create_admin')`

3. **`create_superadmin.py`** - автономный Python скрипт

#### Для преподавателя:

1. **`courses/views.py`** - функция `create_teacher()`

   - Создает преподавателя с указанными данными
   - Расположение: после функции `create_admin()`

2. **`courses/urls.py`** - URL маршрут

   - `path('create_teacher/', views.create_teacher, name='create_teacher')`

3. **`create_teacher.py`** - автономный Python скрипт

---

## Логика работы

### При создании администратора:

- Если пользователь `timaadmin` не существует → создается новый суперпользователь
- Если пользователь уже существует → пароль обновляется, права устанавливаются

### При создании преподавателя:

- Если пользователь с email `teacheer@gmail.com` не существует → создается новый пользователь и профиль преподавателя
- Если пользователь уже существует → обновляются данные пользователя и профиля преподавателя

---

## Проверка работы

### Администратор:

1. Войти в админ-панель: `https://study-task.kz/admin/`

   - Логин: `timaadmin`
   - Пароль: `admin2010`

2. Проверить через Django shell:

```python
python manage.py shell
>>> from courses.models import User
>>> user = User.objects.get(username='timaadmin')
>>> user.is_superuser
True
```

### Преподаватель:

1. Войти в панель преподавателя: `https://study-task.kz/teacher_dashboard/`

   - Логин: `teacheer@gmail.com`
   - Пароль: `teacher2010`

2. Проверить через Django shell:

```python
python manage.py shell
>>> from courses.models import Teacher, User
>>> user = User.objects.get(email='teacheer@gmail.com')
>>> user.is_teacher
True
>>> teacher = Teacher.objects.get(email='teacheer@gmail.com')
>>> teacher.full_name
'Учитель Учитель'
```

---

## Безопасность

⚠️ **Важное предупреждение:**

Эндпоинты `/create_admin/` и `/create_teacher/` не требуют аутентификации и могут создать пользователей любому, кто откроет ссылку.

**Рекомендации:**

- После создания пользователей рекомендуется удалить или защитить эти эндпоинты
- Можно добавить проверку на переменную окружения или секретный ключ
- Или ограничить доступ по IP адресу

**Пример защиты через переменную окружения:**

```python
import os

def create_admin(request):
    secret_key = request.GET.get('key', '')
    if secret_key != os.getenv('ADMIN_CREATION_KEY', 'your-secret-key'):
        return HttpResponse('Access Denied', status=403)
    # ... остальной код
```

Тогда URL будет: `https://study-task.kz/create_admin/?key=your-secret-key`

Аналогично для `create_teacher`.

---

## Структура моделей

### User (Пользователь)

- Базовый класс пользователя Django
- Дополнительные поля: `is_student`, `is_admin`, `is_teacher`

### Teacher (Преподаватель)

- OneToOne связь с User
- Поля: `first_name`, `last_name`, `email`, `phone_number`, `specialization`, `bio`, `avatar`

---

**Создано:** 2024  
**Автор:** AI Assistant
