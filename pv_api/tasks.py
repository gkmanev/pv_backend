from celery import shared_task
from pv_api.utils import fetch_and_store_pv_data

@shared_task
def task_fetch_and_store_pv_data():
    fetch_and_store_pv_data()
    