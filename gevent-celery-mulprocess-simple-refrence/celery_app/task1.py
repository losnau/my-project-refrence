import time
from celery_app import app


@app.task
def num_add(x, y):
    time.sleep(2)
    # return "x:{},y:{},x+y={}".format(x, y, x + y)
    return {"x": x, "y": y, "x+y": x + y}
