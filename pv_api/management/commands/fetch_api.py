from django.core.management.base import BaseCommand
from pv_api.models import PvData
from pv_api.utils import fetch_and_store_pv_data

class Command(BaseCommand):
    help = 'fetch data from API and store in database'

    def handle(self, *args, **kwargs):
        fetch_and_store_pv_data()             
        self.stdout.write(self.style.SUCCESS('Fetched and stored data successfully'))
