from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData
import paramiko
from datetime import datetime, timedelta
import json
import os

from pv_api.helper import OneDriveDataProcessor



class Command(BaseCommand):
    help = 'Fetch data from One Drive and store it in the database'

    def handle(self, *args, **kwargs):  
        test = OneDriveDataProcessor()
        #test.dropbox_downloader()
        #test.extract_downloaded_files()
        test.filter_extracted_files_and_process_data()

        