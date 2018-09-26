from celery import Celery

app = Celery("telnet_cmd")
app.config_from_object('celery_app.celery_config')