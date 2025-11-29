# Инструкция по созданию суперпользователя

## Описание

Система позволяет создать суперпользователя с логином `timaadmin` и паролем `admin2010` несколькими способами.

---

## Способ 1: Через URL (Рекомендуется) ⭐

Самый простой способ - просто открыть ссылку в браузере:

**URL:** `https://study-task.kz/create_admin`

При открытии ссылки:

- Если пользователь `timaadmin` не существует - он будет создан
- Если пользователь уже существует - пароль будет обновлен на `admin2010`, права суперпользователя будут установлены

**Параметры создаваемого пользователя:**

- **Логин:** `timaadmin`
- **Пароль:** `admin2010`
- **is_superuser:** `True`
- **is_staff:** `True`
- **is_admin:** `True`
- **is_active:** `True`

---

## Способ 2: Через Python скрипт

Запустите скрипт из корня проекта:

```bash
python create_superadmin.py
```

Или через Django shell:

```bash
python manage.py shell < create_superadmin.py
```

---

## Способ 3: Через Django Management команду

1. Создайте файл: `courses/management/commands/create_admin.py`
2. Скопируйте содержимое из `create_admin_management_command.py`
3. Запустите команду:

```bash
python manage.py create_admin
```

---

## Технические детали

### Файлы проекта:

1. **`courses/views.py`** - содержит функцию `create_admin()`

   - Функция: `def create_admin(request)`
   - Расположение: конец файла (после строки 4666)

2. **`courses/urls.py`** - содержит URL маршрут

   - URL: `path('create_admin/', views.create_admin, name='create_admin')`
   - Расположение: после колеса фортуны (строка 167)

3. **`create_superadmin.py`** - автономный Python скрипт
   - Можно запускать независимо
   - Настраивает Django окружение автоматически

---

## Безопасность

⚠️ **Важное предупреждение:**

Эндпоинт `/create_admin/` не требует аутентификации и может создать администратора любому, кто откроет ссылку.

**Рекомендации:**

- После создания первого администратора рекомендуется удалить или защитить этот эндпоинт
- Можно добавить проверку на переменную окружения или секретный ключ
- Или ограничить доступ по IP адресу

**Пример защиты через переменную окружения:**

```python
import os

def create_admin(request):
    # Проверка секретного ключа
    secret_key = request.GET.get('key', '')
    if secret_key != os.getenv('ADMIN_CREATION_KEY', 'your-secret-key'):
        return HttpResponse('Access Denied', status=403)

    # ... остальной код
```

Тогда URL будет: `https://study-task.kz/create_admin/?key=your-secret-key`

---

## Проверка работы

После создания администратора вы можете:

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
>>> user.is_staff
True
```

---

## Логи

Функция создает пользователя с правами:

- ✅ Суперпользователь (is_superuser)
- ✅ Доступ в админ-панель (is_staff)
- ✅ Администратор системы (is_admin)
- ✅ Активный пользователь (is_active)

---

**Создано:** 2024  
**Автор:** AI Assistant
