from celery import shared_task
from pv_api.utils import fetch_and_store_pv_data
from datetime import datetime

@shared_task
def task_fetch_and_store_pv_data():
    fetch_and_store_pv_data()
    

# @shared_task
# def task_min_max_intervals(start):
#     start_date = datetime.strptime(start, '%Y-%m-%d').date()    
#     print(f'Start_date: {start_date}')
#     calculate_min_max_intervals(start_date)