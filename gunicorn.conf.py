"""Gunicorn config pour Render - SOFAENGA"""

# Serveur
bind = "0.0.0.0:$PORT"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120

# Logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "sofaenga"

# Sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Keep-alive
keepalive = 5

# Preload
preload_app = True

# User/Group (Render)
user = "www-data"
group = "www-data"

# PID
pidfile = "/tmp/gunicorn.pid"
daemon = False