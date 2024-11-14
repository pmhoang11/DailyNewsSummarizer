import schedule
import time

from app.mq_main import celery_execute
from app.define import settings


first_run = True

def job():
    global first_run

    celery_execute.send_task(
        name="{}.{}".format(settings.AI_QUERY_NAME, settings.SCHEDULE_TASK),
        queue=settings.AI_QUERY_NAME
    )
    if first_run:
        first_run = False
        schedule.clear('job')
        schedule.every(1).hours.do(job).tag('job')

schedule.every(5).seconds.do(job).tag('job')


while True:
    schedule.run_pending()
    time.sleep(1)
