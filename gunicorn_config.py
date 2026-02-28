# Gunicorn configuration file for Django deployment on Render.com

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000

# Timeout settings
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 100

# Django settings
raw_env = [
    'DJANGO_SETTINGS_MODULE=online_courses.settings',
]

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'study_task'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None

# SSL (if needed)
keyfile = None
certfile = None

# Preload application for better performance
preload_app = True

# Graceful shutdown
graceful_timeout = 30
