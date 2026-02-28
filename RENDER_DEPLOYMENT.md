# Render.com Deployment Instructions for Django Project

## Problem
The error `ModuleNotFoundError: No module named 'app'` occurs because Render.com is trying to run `gunicorn app:app` which is for Flask apps, not Django.

## Solution

### 1. Change Start Command in Render.com
In your Render.com dashboard, go to your service settings and change the **Start Command** to:

```bash
gunicorn online_courses.wsgi:application
```

### 2. Alternative: Use gunicorn with config file
Create a `gunicorn_config.py` file in your project root:

```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Django settings
raw_env = [
    'DJANGO_SETTINGS_MODULE=online_courses.settings',
]

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

Then use start command:
```bash
gunicorn -c gunicorn_config.py online_courses.wsgi:application
```

### 3. Make sure your project structure is correct:
```
st-app/
├── online_courses/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── courses/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── manage.py
└── requirements.txt
```

### 4. Verify requirements.txt includes:
```
gunicorn>=20.1.0
django>=5.0.0
```

### 5. Environment Variables in Render.com
Make sure to set these environment variables in Render.com:
- `DJANGO_SETTINGS_MODULE=online_courses.settings`
- `SECRET_KEY=your-secret-key`
- `DEBUG=False` (for production)
- Any other required environment variables

### 6. Build Command (if needed)
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

## Quick Fix
The most important change is the **Start Command**:
Change from: `gunicorn app:app`
To: `gunicorn online_courses.wsgi:application`

This tells Gunicorn to use the Django WSGI application instead of looking for a Flask app.
